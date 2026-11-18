[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputDirectory,
    [ValidateSet('X25519', 'kyber768', 'p384_kyber768')][string]$KeyExchange = 'X25519',
    [ValidateRange(1, 60)][int]$MeasurementSeconds = 5,
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$null = Get-Command python -ErrorAction Stop
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $OutputDirectory) {
    throw 'Choose a new output directory; existing results are never overwritten.'
}
$null = New-Item -ItemType Directory -Path "$OutputDirectory/client", "$OutputDirectory/server"
$logPath = Join-Path $OutputDirectory 'docker.log'
$composeArgs = @('compose', '--project-name', 'pqc-conext2023', '--file', "$PSScriptRoot/docker-compose.yml")
$settings = @{
    CPU_PROFILING = 'False'; RUN = '000'; KEM_ALG = $KeyExchange
    SIG_ALG = 'rsa:2048'; NETEM_TC = ''; HOST_DIR = $OutputDirectory
    OUT_DIR = $OutputDirectory; EXPERIMENT = 'initial-smoke'; DEVIATION_ANALYSIS = 'False'
}
$previousEnvironment = @{}
foreach ($name in $settings.Keys) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    [Environment]::SetEnvironmentVariable($name, $settings[$name], 'Process')
}

function Invoke-SmokeCompose([string[]]$DockerArguments) {
    & docker @composeArgs @DockerArguments *>> $logPath
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed: $($DockerArguments -join ' '). See $logPath"
    }
}

$started = $false
try {
    $existing = & docker @composeArgs ps --all --quiet 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose is unavailable.' }
    if ($existing) { throw 'The pqc-conext2023 project is already in use.' }
    Invoke-SmokeCompose @('config', '--quiet')
    if (-not $SkipBuild) {
        Write-Host 'Building the upstream client/server image...'
        Invoke-SmokeCompose @('build', 'client', 'server')
    }
    Write-Host "Starting $KeyExchange with RSA-2048 authentication..."
    $started = $true
    Invoke-SmokeCompose @('up', '--detach', '--no-build', 'server')
    $deadline = [DateTime]::UtcNow.AddSeconds(60)
    do {
        $serverLog = & docker @composeArgs logs --no-color server 2>$null
        if (($serverLog -join "`n") -match 'ACCEPT') { break }
        if ([DateTime]::UtcNow -gt $deadline) { throw 'TLS server did not become ready in 60 seconds.' }
        Start-Sleep -Seconds 1
    } while ($true)

    Invoke-SmokeCompose @('run', '--rm', '--no-deps', '-T', '--env', "MEASUREMENT_TIME=$MeasurementSeconds", 'client')
    # Flush the server capture before Docker stops its shell entry point.
    Invoke-SmokeCompose @('exec', '-T', 'server', 'pkill', '-INT', 'tcpdump')
    Invoke-SmokeCompose @('stop', 'server')
    $stdout = Get-Content -LiteralPath "$OutputDirectory/client/opensslclient_run000.stdout" -Raw
    $connections = [regex]::Match($stdout, '(\d+) connections in ([\d.]+)s; ([\d.]+|inf) connections/user sec')
    $elapsed = [regex]::Match($stdout, 'in ([\d.]+) real seconds')
    if (-not $connections.Success -or -not $elapsed.Success -or [int]$connections.Groups[1].Value -le 0) {
        throw 'The client did not report a successful measurement.'
    }
    & python "$PSScriptRoot/validate_pcaps.py" "$OutputDirectory/client/latencies-post_run000.pcap" "$OutputDirectory/server/latencies-pre_run000.pcap" > "$OutputDirectory/pcap-validation.json"
    if ($LASTEXITCODE -ne 0) { throw 'Packet capture validation failed.' }
    $seconds = [double]::Parse($elapsed.Groups[1].Value, [Globalization.CultureInfo]::InvariantCulture)
    if ($seconds -le 0) { throw 'Invalid elapsed time.' }
    $result = [ordered]@{
        key_exchange = $KeyExchange; signature = 'rsa:2048'; tls_mode = 'server-authenticated'
        measurement_seconds_requested = $MeasurementSeconds
        connections = [int]$connections.Groups[1].Value; real_seconds_reported = $seconds
        connections_per_real_second = [math]::Round([int]$connections.Groups[1].Value / $seconds, 3)
        netem = ''; cpu_profiling = $false
        source_commit = (& git -C $PSScriptRoot rev-parse HEAD)
        source_modified_files = @(& git -C $PSScriptRoot status --porcelain)
        launcher_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
        image_id = (& docker image inspect pqc-conext2023-client --format '{{.Id}}')
        validation_only = $true
    }
    $result | ConvertTo-Json | Set-Content -LiteralPath "$OutputDirectory/result.json" -Encoding utf8
    [pscustomobject]$result | Export-Csv -LiteralPath "$OutputDirectory/result.csv" -NoTypeInformation -Encoding utf8
    Write-Host "PASS: $($result.connections) connections; results in $OutputDirectory"
} finally {
    if ($started) {
        & docker @composeArgs logs --no-color server *>> $logPath
        & docker @composeArgs down --volumes *>> $logPath
        if ($LASTEXITCODE -ne 0) { Write-Warning "Cleanup failed. See $logPath" }
    }
    foreach ($name in $settings.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}

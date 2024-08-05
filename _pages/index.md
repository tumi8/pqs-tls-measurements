---
layout: page
permalink: /
title: "The Performance of Post-Quantum TLS1.3"
description: "This page describes the artifacts and published data necessary to reproduce the findings of the paper: \"The Performance of Post-Quantum TLS1.3\", a collobaration between TUM and Nokia Bell Labs."
---

The paper was published at the **[CoNEXT 2023](https://conferences2.sigcomm.org/co-next/2023)** and can be found online under [DOI:10.1145/3624354.3630585](https://doi.org/10.1145/3624354.3630585).

**Authors:**
{% for author in site.data.authors.list %}<a style="border-bottom: none" href="https://orcid.org/{{author.orcid}}">
<img src="assets/ORCIDiD_icon16x16.png" style="width: 1em; margin-inline-start: 0.5em;" alt="ORCID iD icon"/></a>
[{{author.name}}](https://orcid.org/{{author.orcid}}){% if author.name contains "Sgan" %}{% else %}, {% endif %}
{% endfor %}

<div class="accordion-box">
  <div class="accordion-box__title">
    Abstract
  </div>
  <div class="accordion-box__content">
      <p>Quantum Computers (QCs) differ radically from traditional computers and can efficiently solve mathematical problems fundamental to our current cryptographic algorithms. Although existing QCs need to accommodate more qubits to break cryptographic algorithms, the concern of ''Store-Now-Decrypt-Later'' (i.e., adversaries store encrypted data today and decrypt them once powerful QCs become available) highlights the necessity to adopt quantum-safe approaches as soon as possible. In this work, we investigate the performance impact of Post-Quantum Cryptography (PQC) on TLS 1.3. Different signature algorithms and key agreements (as proposed by the National Institute of Standards and Technology (NIST)) are examined through black- and white-box measurements to get precise handshake latencies and computational costs per participating library. We emulated loss, bandwidth, and delay to analyze constrained environments. Our results reveal that HQC and Kyber are on par with our current state-of-the-art, while Dilithium and Falcon are even faster. We observed no performance drawback from using hybrid algorithms; moreover, on higher NIST security levels, PQC outperformed any algorithm in use today. Hence, we conclude that post-quantum TLS is suitable for adoption in today's systems.</p>
  </div>
</div><br>

We provide access to the following artifacts:
- A docker setup to reproduce most of our experiments. It is a simplified 2-node setup that can run in arbitrary environments, although, results might differ because of the containers, virtualized networks, traffic capturing only with software, and the different underlying hardware. The scripts can be found at <a href="https://github.com/tumi8/pqs-tls-measurements">our main Github Repository</a>.
- The raw measurements data obtained in our 3-node setup using hardware timestamping. It is available on <a href="https://mediatum.ub.tum.de/1725057">MediaTUM</a>, or <a href="https://doi.org/10.14459/2023mp1725057">DOI:10.14459/2023mp1725057</a>.</li>
- Evaluation scripts to reproduce our analyses, also at our [main Github Repository]({{ site.repository }}).
  They can be used both together with results from a local docker experiments or our published data.
  Using the latter as input allows to reproduce the exact findings from our paper.
- The used OpenSSL Fork found at our <a href="https://github.com/tumi8/openssl-pqc">TUM I8 OpenSSL Repository</a>, containing a fork of the Open Quantum Safe's OpenSSL version.

You can cite our work using the following template:

Markus Sosnowski, Florian Wiedner, Eric Hauser, Lion Steger, Dimitrios Schoinianakis, Sebastian Gallenmüller, and Georg Carle. 2023.
**The Performance of Post-Quantum TLS 1.3**. In *Proceedings of the International Conference on emerging Networking EXperiments and Technologies (CoNEXT ’23)*. Paris, France.

```bib
{% raw %}@inproceedings{SosnowskiPQTLS23,
    title = {{The Performance of Post-Quantum TLS 1.3}},
    author = { Sosnowski, Markus and Wiedner, Florian and Hauser, Eric and Steger, Lion and Schoinianakis, Dimitrios and Gallenm{\"u}ller, Sebastian and Carle, Georg},
    booktitle = {Proceedings of the International Conference on emerging Networking EXperiments and Technologies (CoNEXT '23)},
    year = {2023},
    address = {Paris, France},
    month = dec,
    keywords = {performance measurements, post-quantum cryptography},
    homepage = {https://tumi8.github.io/pqs-tls-measurements},
    doi = {10.1145/3624354.3630585},
}{% endraw %}
```

manynines=9
n=30
lst=[0.05, 0.25, 0.5, 0.75, 0.95]

start = 1.0
stepper = start
end = start
for i in range(0, manynines):
    end = start * 10.0
    diff = (end - start) / n
    #lst.append(start)
    for i in range (0, n):
        print(start)
        lst.append((start-1)/start)
        start += diff
    #lst.append(end)
    start = end

print(sorted(lst))

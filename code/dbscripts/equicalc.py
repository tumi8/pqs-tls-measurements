manynines=9
n=10
lst=[0.05, 0.25, 0.5, 0.75, 0.9]

def calcPerc(start, end):
    k = (end/start)**(1/(n-1))
    ls = []
    for i in range(1, n-1):
        ls.append(start*k**i)
    return ls+[end]

start = 0.9
stepper = start
end = start
for i in range(0, manynines-2):
    stepper = stepper / 10
    end += stepper
    lst += calcPerc(start, end)
    start = end

print(lst)

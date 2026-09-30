import pandas as pd
import numpy as np

# Required information
a = 0  # lower bound
b = 2  # upper bound


def f(x):
    return x * np.sin(x) - 1  # the function from the problem


iter_max = 50  # maximum allowed iterations
tol_max = 0.00000005  # acceptable error tolerance

# initial condition
i = 1

# creating a container for iteration results
results = pd.DataFrame(columns=["n", "a", "b", "c"])

# iterations start here
while i <= iter_max and (b - a) / 2 > tol_max:
    p = a + ((b - a) / 2)  # taking the value of p, the midpoint between a and b
    FP = f(p)  # evaluate f(p)
    FA = f(a)  # evaluate f(a)
    FB = f(b)  # evaluate f(b)
    results.loc[i] = [i, a, b, p]  # store the calculation results in the container
    if FA * FP < 0:
        b = p
    else:
        a = p  # recall the bisection rule!
    i = i + 1  # increment i for iteration

print(results)

from sympy import symbols, diff

# Define the symbol
x = symbols("x")

# Define the equation
eq = x**3 - x**2 - 70

# Differentiate the equation with respect to x
diff_eq = diff(eq, x)

# Convert the differentiated equation to a string
diff_eq_str = str(diff_eq)

print(diff_eq_str)

import pandas as pd
import numpy as np

# Define the necessary information
x_0 = 10


def f(x):
    return x**3 - x**2 - 70


def df(x):
    return 3 * x**2 - 2 * x


iter_max = 50
tol_max = 10**-2

# initial condition
i = 1
hasil = pd.DataFrame(columns=["n_iter", "p"], index=[0])
hasil.loc[0] = [0, x_0]

while i <= iter_max:
    p = x_0 - (f(x_0) / df(x_0))
    hasil.loc[i] = [i, p]
    if abs(p - x_0) < tol_max:
        break
    x_0 = p
    i += 1

# print output
print(hasil.to_string(index=False))

import numpy as np
import matplotlib.pyplot as plt


# Define the function
def f(x):
    return x**3 - 10 * x**2 + 29 * x - 20


# Generate x values
x = np.linspace(0, 6, 400)  # 400 points between 0 and 6

# Generate y values
y = f(x)

# Create the plot
plt.figure(figsize=(8, 6))
plt.plot(x, y, label=r"$f(x) = x^3 - 10x^2 + 29x - 20$")

# Add labels and title
plt.xlabel("x")
plt.ylabel("f(x)")
plt.title("Graph of $f(x) = x^3 - 10x^2 + 29x - 20$")

# Add grid
plt.grid(True)

# Add legend
plt.legend()

# Show plot
plt.show()

from math import sqrt

# define r as the golden ratio
r = (1 + sqrt(5)) / 2
tol_max = 10 ** (-10)


# Define the problem function
def f_initial(x):
    return x**3 - 10 * x**2 + 29 * x - 20


def f(x):
    return abs(x**3 - 10 * x**2 + 29 * x - 20)


# initial values
def golden_ss(a=0, b=2):
    while abs(b - a) > tol_max:
        c = b - (b - a) / r
        d = a + (b - a) / r

        if f(c) < f(d):
            b = d
        else:
            a = c

    return (a + b) / 2


print(golden_ss(0, 2))
print(golden_ss(3.5, 4.5))
print(golden_ss(4.5, 6))

import matplotlib.pyplot as plt


def logistic_map(r, x0, steps):
    results = [x0]
    for _ in range(1, steps):
        x = results[-1]
        next_x = r * x * (1 - x)
        results.append(next_x)
    return results


# Parameters
r = 3.9  # Growth rate parameter
x0 = 0.4  # Initial population
steps = 100

# Simulate the logistic map
population = logistic_map(r, x0, steps)

# Plot the results
plt.plot(range(steps), population, linestyle="-", marker="o", color="b")
plt.title("Logistic Map (Chaotic System)")
plt.xlabel("Time Step")
plt.ylabel("Population")
plt.grid(True)
plt.show()

import random


def coin_toss(num_tosses):
    outcomes = []
    for _ in range(num_tosses):
        outcome = random.choice(["Heads", "Tails"])
        outcomes.append(outcome)
    return outcomes


# Parameters
num_tosses = 100

# Simulate coin tosses
outcomes = coin_toss(num_tosses)

# Counting the occurrence of Heads and Tails
heads_count = outcomes.count("Heads")
tails_count = outcomes.count("Tails")

# Display results
print(f"Heads: {heads_count} Tails: {tails_count}")

import matplotlib.pyplot as plt
import numpy as np

# Parameters
R = 100  # Reward amount
r = 0.10  # Discount rate (for exponential)
k = 0.10  # Discount rate (for hyperbolic)
t = np.linspace(0, 20, 100)  # Time from 0 to 20 years

# Discounting formulas
V_exp = R / (1 + r) ** t
V_hyp = R / (1 + k * t)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(t, V_exp, label="Exponential Discounting", color="blue")
plt.plot(t, V_hyp, label="Hyperbolic Discounting", color="orange", linestyle="--")

plt.title("Exponential vs. Hyperbolic Discounting ($100 Reward)")
plt.xlabel("Time (years)")
plt.ylabel("Present Value ($)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad, simpson
import random

# ===== USER INPUTS ===== #
num_servers = int(input("Enter number of servers: "))
servers = []
for i in range(num_servers):
    print("\nServer {} Configuration:".format(i+1))
    name = input("  Name (e.g., 'Server-1 (NY)'): ")
    capacity = float(input("  Capacity (max requests/sec): "))
    base_load = float(input("  Base load (requests/sec): "))
    amplitude = float(input("  Amplitude (for load fluctuations): "))
    latency = float(input("  Latency (ms): "))
    servers.append({
        "name": name,
        "capacity": capacity,
        "base_load": base_load,
        "amplitude": amplitude,
        "latency": latency
    })

# ===== SIMULATION SETUP ===== #
T = 24  # Time range (hours)
steps = 1000
t_values = np.linspace(0, T, steps)

# ===== LOAD MODELING ===== #
def server_load(t, server):
    """Generates realistic load with stochastic bursts."""
    periodic_load = server["base_load"] + server["amplitude"] * np.sin(np.pi * (t + random.uniform(0, 4)) / 12)
    burst_prob = 0.02  # 2% chance of a traffic burst
    burst = 40 * np.random.poisson(burst_prob)
    noise = np.random.normal(0, 5)  # Random fluctuations
    return min(periodic_load + burst + noise, server["capacity"])

# Evaluate loads over time
loads = np.array([[server_load(t, server) for t in t_values] for server in servers])

# ===== LOAD BALANCING ANALYSIS ===== #
def calculate_imbalance(loads):
    """Computes imbalance metric using integral of squared deviations."""
    avg_load = np.mean(loads, axis=0)
    imbalance = np.sum((loads - avg_load) ** 2, axis=0)
    total_imbalance = simpson(imbalance, t_values)
    return imbalance, total_imbalance

imbalance, total_imbalance = calculate_imbalance(loads)

# ===== DYNAMIC LOAD REDISTRIBUTION ===== #
def redistribute_load(loads, threshold=30):
    """Shifts load if imbalance exceeds threshold."""
    avg_load = np.mean(loads, axis=0)
    redistributed = loads.copy()
    for i in range(len(t_values)):
        if imbalance[i] > threshold:
            overloaded = np.argmax(loads[:, i])
            underloaded = np.argmin(loads[:, i])
            transfer = min(loads[overloaded, i] - avg_load[i], avg_load[i] - loads[underloaded, i])
            redistributed[overloaded, i] -= transfer
            redistributed[underloaded, i] += transfer
    return redistributed

redistributed_loads = redistribute_load(loads)
_, new_imbalance = calculate_imbalance(redistributed_loads)

# ===== VISUALIZATION ===== #
plt.figure(figsize=(14, 8))

# Plot original loads
plt.subplot(2, 2, 1)
for i, server in enumerate(servers):
    plt.plot(t_values, loads[i], label=server["name"])
plt.title("Original Server Loads")
plt.xlabel("Time (hours)")
plt.ylabel("Load (requests/sec)")
plt.legend()
plt.grid()

# Plot imbalance
plt.subplot(2, 2, 2)
plt.plot(t_values, imbalance, 'r-', label="Imbalance")
plt.axhline(y=30, color='gray', linestyle='--', label="Threshold")
plt.title("Load Imbalance Over Time")
plt.xlabel("Time (hours)")
plt.ylabel("Imbalance Metric")
plt.legend()
plt.grid()

# Plot redistributed loads
plt.subplot(2, 2, 3)
for i, server in enumerate(servers):
    plt.plot(t_values, redistributed_loads[i], label=server["name"])
plt.title("Loads After Redistribution")
plt.xlabel("Time (hours)")
plt.ylabel("Load (requests/sec)")
plt.legend()
plt.grid()

# Plot imbalance comparison
plt.subplot(2, 2, 4)
plt.bar(["Original", "Redistributed"], [total_imbalance, new_imbalance], color=['red', 'green'])
plt.title("Total Imbalance Comparison")
plt.ylabel("Integrated Imbalance")

plt.tight_layout()
plt.show()

# ===== ACTIONABLE INSIGHTS ===== #
print("\n=== LOAD BALANCING REPORT ===")
print("Total Imbalance (Original): {:.2f}".format(total_imbalance))
print("Total Imbalance (After Redistribution): {:.2f}".format(new_imbalance))
print("Improvement: {:.1f}% reduction".format(100 * (total_imbalance - new_imbalance) / total_imbalance))

# Identify peak load times
peak_time = t_values[np.argmax(np.max(loads, axis=0))]
print("\nPeak Load Occurs at: {:.1f} hours".format(peak_time))

# Check for capacity violations
for i, server in enumerate(servers):
    overload = np.any(loads[i] > 0.9 * server["capacity"])
    print("{} was at risk of overload: {}".format(server['name'], 'YES' if overload else 'NO'))

# compute_deflections.py

import numpy as np
import matplotlib.pyplot as plt
import csv
import itertools
from beam_library import BeamLibrary, Beam, Material, Load
import matplotlib as mpl

def y1(x, E1, I, L, w):
    """
    Deflection equation y1(x) for 0 <= x < T (Distributed Load)
    """
    return (-w / (24 * E1 * I)) * (L - x)**4 - (w * L**3) / (6 * E1 * I) * x + (w * L**4) / (24 * E1 * I)

def y2(x, E1, E2, I, L, T, w):
    """
    Deflection equation y2(x) for T <= x <= L (Distributed Load)
    """
    term1 = (-w) / (24 * E2 * I) * (L - x)**4
    coefficient = (-w) / (6 * I) * ((L**3 - (L - T)**3)/E1 + (L - T)**3 / E2)
    term2 = coefficient * x
    term3 = (w / (24 * E1 * I)) * (L**4 - (L - T)**4 - 4 * L**3 * T)
    term4 = (w / (24 * E2 * I)) * (L - T)**4
    term5 = -coefficient * T
    return term1 + term2 + term3 + term4 + term5

def theta1(x, E1, I, L, w):
    """
    Angular deflection theta1(x) for 0 <= x < T (Distributed Load)
    """
    return (w / (6 * E1 * I)) * (L - x)**3 - (w * L**3) / (6 * E1 * I)

def theta2(x, E1, E2, I, L, T, w):
    """
    Angular deflection theta2(x) for T <= x <= L (Distributed Load)
    """
    term1 = (w / (6 * E2 * I)) * (L - x)**3
    coefficient = (-w) / (6 * I) * ((L**3 - (L - T)**3)/E1 + (L - T)**3 / E2)
    return term1 + coefficient

def y_point_load(x, P, E1, I, y):
    """
    Deflection equation y(x) for Point Load
    """
    if x < y:
        return (P / (2 * E1 * I)) * (y * x**2 - (x**3) / 3)
    else:
        return (P * y**2) / (2 * E1 * I) * (x - y)

def theta_point_load(x, P, E1, I, y):
    """
    Angular deflection theta(x) for Point Load
    """
    if x < y:
        return - (P / (E1 * I)) * (y * x - (x**2) / 2)
    else:
        return - (P * y**2) / (2 * E1 * I)

def compute_deflections(library: BeamLibrary, output_filename: str = "deflection_results.csv"):
    """
    Computes deflection and angular deflection results for all unique combinations of materials and loads,
    and writes the results to a CSV file.
    Returns a dictionary of transition points for each beam.
    """
    materials = library.get_materials()
    beams = library.get_beams()
    loads = library.get_loads()

    # Debugging: Print counts
    print(f"Loaded {len(materials)} materials.")
    print(f"Loaded {len(beams)} beams.")
    print(f"Loaded {len(loads)} loads.")

    if not beams:
        print("No beams defined in the library. Exiting deflection computation.")
        return {}

    if not loads:
        print("No loads defined in the library. Exiting deflection computation.")
        return {}

    if not materials:
        print("No materials defined in the library. Exiting deflection computation.")
        return {}

    # Define x range with increments of 0.0025m
    step = 0.0025

    # Prepare CSV file
    with open(output_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(['Beam', 'Load', 'Material1', 'Material2', 'x (m)', 'y(x) (m)', 'theta(x) (degrees)'])

        # Dictionary to store transition points
        transition_points = {}

        # Iterate over all combinations of beams, loads, materials (E1 and E2)
        for beam in beams:
            I = beam.moment_of_inertia()
            L = beam.length

            print(f"\n--- Configuring Beam: {beam.name} ---")

            for load in loads:
                print(f"\nApplying Load: {load.name} (Type: {load.load_type.capitalize()})")

                # Determine if the load is distributed or point
                if load.load_type == "distributed":
                    w = load.w
                    # Prompt user for Transition Point T for this beam
                    while True:
                        try:
                            T_input = input(f"Enter the Transition Point T [m] for Beam '{beam.name}' (0 < T < {L}): ").strip()
                            T = float(T_input)
                            if 0 < T < L:
                                # For distributed loads, no additional checks
                                transition_points.setdefault(beam.name, []).append(T)
                                break
                            else:
                                print(f"Transition Point T must be between 0 and {L} meters.")
                        except ValueError:
                            print("Invalid input. Please enter a numerical value for T.")

                    # Iterate over all combinations of E1 and E2
                    for material1, material2 in itertools.product(materials, repeat=2):
                        E1 = material1.E
                        E2 = material2.E

                        # Define x values from 0 to L with step 0.0025m
                        x_values = np.arange(0, L + step, step)

                        for x in x_values:
                            if x < T:
                                y = y1(x, E1, I, L, w)
                                theta = theta1(x, E1, I, L, w)
                            else:
                                y = y2(x, E1, E2, I, L, T, w)
                                theta = theta2(x, E1, E2, I, L, T, w)
                            # Convert theta from radians to degrees
                            theta_degrees = np.degrees(theta)
                            # Round x, y, and theta for better readability
                            writer.writerow([beam.name, load.name, material1.name, material2.name,
                                             round(x, 4), y, round(theta_degrees, 6)])

                elif load.load_type == "point":
                    P = load.P
                    y_load = load.a

                    # Ensure the point load position is within the beam
                    if not (0 < y_load < L):
                        print(f"Warning: Point load position a = {y_load} m is outside the beam length ({L} m). Skipping this load.")
                        continue

                    # Prompt user for Transition Point T for this beam
                    while True:
                        try:
                            T_input = input(f"Enter the Transition Point T [m] for Beam '{beam.name}' (must be after point load position y = {y_load} m, and 0 < T < {L}): ").strip()
                            T = float(T_input)
                            if 0 < T < L:
                                if T < y_load:
                                    print(f"Warning: Transition Point T = {T} m is before the point load position y = {y_load} m. Results may not be representative.")
                                # Store the transition point
                                transition_points.setdefault(beam.name, []).append(T)
                                break
                            else:
                                print(f"Transition Point T must be between 0 and {L} meters.")
                        except ValueError:
                            print("Invalid input. Please enter a numerical value for T.")

                    # Iterate over all combinations of E1 and E2
                    for material1, material2 in itertools.product(materials, repeat=2):
                        E1 = material1.E
                        E2 = material2.E  # Note: For point loads, E2 might not be used unless modeling multiple materials beyond T

                        # Define x values from 0 to L with step 0.0025m
                        x_values = np.arange(0, L + step, step)

                        for x in x_values:
                            if x < y_load:
                                y = y_point_load(x, P, E1, I, y_load)
                                theta = theta_point_load(x, P, E1, I, y_load)
                            else:
                                y = y_point_load(x, P, E1, I, y_load)  # Deflection is continuous across y_load
                                theta = theta_point_load(x, P, E1, I, y_load)
                            # Convert theta from radians to degrees
                            theta_degrees = np.degrees(theta)
                            # Round x, y, and theta for better readability
                            writer.writerow([beam.name, load.name, material1.name, material2.name,
                                             round(x, 4), y, round(theta_degrees, 6)])
                else:
                    print(f"Unsupported load type: {load.load_type}. Skipping this load.")

    print(f"\nDeflection and angular deflection results have been written to '{output_filename}'.")
    return transition_points

def plot_deflections(library: BeamLibrary, transition_points: dict):
    """
    Generates deflection curve plots for each beam.
    Each plot contains separate curves for each unique material combination.
    The y-axis represents angular deflection theta(x) in degrees.
    """
    materials = library.get_materials()
    beams = library.get_beams()
    loads = library.get_loads()

    if not beams:
        print("No beams defined in the library. Exiting plot generation.")
        return

    if not loads:
        print("No loads defined in the library. Exiting plot generation.")
        return

    if not materials:
        print("No materials defined in the library. Exiting plot generation.")
        return

    # Iterate over each beam
    for beam in beams:
        I = beam.moment_of_inertia()
        L = beam.length

        print(f"\n--- Plotting Angular Deflection for Beam: {beam.name} ---")

        # Retrieve stored Transition Points T
        Ts = transition_points.get(beam.name, [])

        # Iterate over each load applied to this beam
        for load in loads:
            if load.load_type == "distributed":
                if not Ts:
                    print(f"No Transition Point T found for Beam '{beam.name}' and Load '{load.name}'. Skipping plot for this load.")
                    continue
                T = Ts.pop(0)  # Assuming one T per load per beam

                w = load.w
                print(f"Plotting for Distributed Load '{load.name}' with T = {T} m")

                # Prepare the plot
                plt.figure(figsize=(14, 8))
                plt.title(f"Angular Deflection Curves for Beam: {beam.name} with Load: {load.name}")
                plt.xlabel("Position along beam x (m)")
                plt.ylabel("Angular Deflection θ(x) (degrees)")
                plt.grid(True)

                # Generate a unique color for each material combination
                num_combinations = len(materials) ** 2
                color_cycle = plt.get_cmap('viridis')  # Using 'viridis' for a large number of colors
                colors = [color_cycle(i / num_combinations) for i in range(num_combinations)]

                color_idx = 0  # Index to keep track of colors

                # Iterate over all combinations of E1 and E2
                for material1, material2 in itertools.product(materials, repeat=2):
                    E1 = material1.E
                    E2 = material2.E

                    # Define x values from 0 to L with step 0.0025m
                    x_values = np.arange(0, L + 0.0025, 0.0025)
                    theta_values = []

                    for x in x_values:
                        if x < T:
                            theta = theta1(x, E1, I, L, w)
                        else:
                            theta = theta2(x, E1, E2, I, L, T, w)
                        theta_degrees = np.degrees(theta)
                        theta_values.append(theta_degrees)

                    # Label for the curve
                    label = f"{material1.name} & {material2.name}"
                    # Plot the curve
                    plt.plot(x_values, theta_values, label=label, color=colors[color_idx])
                    color_idx += 1

                # Add legend outside the plot area for clarity
                plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
                plt.tight_layout()
                plt.show()

            elif load.load_type == "point":
                if not Ts:
                    print(f"No Transition Point T found for Beam '{beam.name}' and Load '{load.name}'. Skipping plot for this load.")
                    continue
                T = Ts.pop(0)  # Assuming one T per load per beam

                P = load.P
                y_load = load.a

                print(f"Plotting for Point Load '{load.name}' with T = {T} m and y = {y_load} m")

                # Prepare the plot
                plt.figure(figsize=(14, 8))
                plt.title(f"Angular Deflection Curves for Beam: {beam.name} with Load: {load.name}")
                plt.xlabel("Position along beam x (m)")
                plt.ylabel("Angular Deflection θ(x) (degrees)")
                plt.grid(True)

                # Generate a unique color for each material combination
                num_combinations = len(materials) ** 2
                color_cycle = plt.get_cmap('viridis')  # Using 'viridis' for a large number of colors
                colors = [color_cycle(i / num_combinations) for i in range(num_combinations)]

                color_idx = 0  # Index to keep track of colors

                # Iterate over all combinations of E1 and E2
                for material1, material2 in itertools.product(materials, repeat=2):
                    E1 = material1.E
                    E2 = material2.E  # Note: For point loads, E2 might not be used unless modeling multiple materials beyond T

                    # Define x values from 0 to L with step 0.0025m
                    x_values = np.arange(0, L + 0.0025, 0.0025)
                    theta_values = []

                    for x in x_values:
                        theta = theta_point_load(x, P, E1, I, y_load)
                        theta_degrees = np.degrees(theta)
                        theta_values.append(theta_degrees)

                    # Label for the curve
                    label = f"{material1.name} & {material2.name}"
                    # Plot the curve
                    plt.plot(x_values, theta_values, label=label, color=colors[color_idx])
                    color_idx += 1

                # Add legend outside the plot area for clarity
                plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
                plt.tight_layout()
                plt.show()
            else:
                print(f"Unsupported load type: {load.load_type}. Skipping plot for this load.")

def main():
    # Initialize the library
    library = BeamLibrary()

    # Compute deflections and write to CSV, capturing transition points
    transition_points = compute_deflections(library, output_filename="deflection_results.csv")

    if not transition_points:
        print("No deflection computations were performed.")
        return

    # Generate angular deflection plots using transition points
    plot_deflections(library, transition_points)

    print("\nScript execution completed.")

if __name__ == "__main__":
    main()

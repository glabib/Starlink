# -*- coding: utf-8 -*-
"""solution.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_EN8pn69Rk75aO754Hm6q6sWwHg-3C8U

## **Starlink Beam Planning**

This Python notebook illustrates how to investigate the coverage of a set of given Starlink satellites and a set of users distributed along the globe. The existence of interfering satellites apart from the Starlink satellites set is also investigated and permissible coverage is calculated.
"""

from google.colab import drive
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
# %%writefile solution.py
# 
# #!/usr/bin/python3
# 
# import argparse
# import sys
# from collections import namedtuple
# from math import sqrt, acos, degrees, floor

# A type for our 3D points.
# In this scenario, units are in km.
Vector3 = namedtuple('Vector3', ['x', 'y', 'z'])

# Center of the earth.
origin = Vector3(0,0,0)

# Speed of light, km/s
speed_of_light_km_s = 299792.0

# Beams per satellite.
beams_per_satellite = 32

# List of valid beam IDs.
valid_beam_ids = [str(i) for i in range(1, beams_per_satellite + 1)]

# Colors per satellite.
colors_per_satellite = 4
color = 0

# List of valid color IDs.
valid_color_ids = [chr(ord('A') + i) for i in range(0, colors_per_satellite)]

# Self-interference angle, degrees
self_interference_max = 10.0

# Non-Starlink interference angle, degrees
non_starlink_interference_max = 20.0

# Max user to Starlink beam angle, degrees from vertical.
max_user_visible_angle = 45.0

covered = [0]

parser = argparse.ArgumentParser()
parser.add_argument("-f", help="provide test case filename as argument", required=True)
args = parser.parse_args()
file_name = args.f

def read_file(filename):
    # open test_case file
    with open(filename) as f:
        content = f.readlines()
    # read each line of text file and parse.
    test_cases=[]
    for line in content:
        # if line is \n ignore
        if line[0] == "\n":
            line="#"
        # if line is a comment ignore
        li=line.strip()
        if not li.startswith("#"):
            split_line=li.split(' ')
            line_item=(split_line[0], split_line[1], split_line[2], split_line[3], split_line[4])
            test_cases.append(line_item)
    return test_cases

def read_object(object_type:str, line:str, dest:dict) -> bool:
    """
    Given line, of format 'type id float float float', grabs a Vector3 from the last
    three tokens and puts it into dest[id].

    Returns: Success or failure.
    """
    parts = line.split()
    if parts[0] != object_type or len(parts) != 5:
        print("Invalid line! " + line)
        return False
    else:
        ident = parts[1]
        try:
            x = float(parts[2])
            y = float(parts[3])
            z = float(parts[4])
        except:
            print("Can't parse location! " + line)
            return False

        dest[ident] = Vector3(x, y, z)
        return True

def read_scenario(filename:str, scenario:dict) -> bool:
    """
    Given a filename of a scenario file, and a dictionary to populate, populates
    the dictionary with the contents of the file, doing some validation along
    the way.

    Returns: Success or failure.
    """

    sat_count = 0
    user_count = 0
    interferer_count = 0

    scenariofile_lines = open(filename).readlines()
    scenario['sats'] = {}
    scenario['users'] = {}
    scenario['interferers'] = {}
    for line in scenariofile_lines:
        if "#" in line:
            # Comment.
            continue

        elif line.strip() == "":
            # Whitespace or empty line.
            continue

        elif "interferer" in line:
            # Read a non-starlink-sat object.
            if not read_object('interferer', line, scenario['interferers']):
                return False
            else:
                interferer_count += 1

        elif "sat" in line:
            # Read a sat object.
            if not read_object('sat', line, scenario['sats']):
                return False
            else:
                sat_count += 1

        elif "user" in line:
            # Read a user object.
            if not read_object('user', line, scenario['users']):
                return False
            else:
                user_count += 1

        else:
            print("Invalid line! " + line)
            return False

# =========================================================================
def check_interferer_interference(sat_loc: Vector3, user_loc: Vector3) -> bool:
    """
    Given the scenario and the proposed solution, calculate whether any sat has
    a beam that will interfere with a non-Starlink satellite by placing a beam
    that the user would see as within non_starlink_interference_max of a
    non-Starlink satellite.

    Returns: Success or failure.
    """

    # Iterate over the non-Starlink satellites.
    for interferer in scenario['interferers']:
        interferer_loc = scenario['interferers'][interferer]

        # Calculate the angle the user sees from the Starlink to the not-Starlink.
        angle = calculate_angle_degrees(user_loc, sat_loc, interferer_loc)
        if angle < non_starlink_interference_max:
           # Exit if this link is within the interference threshold.
           return True

    return False
# =========================================================================

def calculate_angle_degrees(vertex: Vector3, point_a: Vector3, point_b: Vector3) -> float:
    """
    Returns: the angle formed between point_a, the vertex, and point_b in degrees.
    """

    # Calculate vectors va and vb
    va = Vector3(point_a.x - vertex.x, point_a.y - vertex.y, point_a.z - vertex.z)
    vb = Vector3(point_b.x - vertex.x, point_b.y - vertex.y, point_b.z - vertex.z)

    # Calculate each vector's magnitude.
    va_mag = sqrt( (va.x ** 2) + (va.y ** 2) + (va.z ** 2) )
    vb_mag = sqrt( (vb.x ** 2) + (vb.y ** 2) + (vb.z ** 2) )

    # Normalize each vector.
    va_norm = Vector3(va.x / va_mag, va.y / va_mag, va.z / va_mag)
    vb_norm = Vector3(vb.x / vb_mag, vb.y / vb_mag, vb.z / vb_mag)

    # Calculate the dot product.
    dot_product = (va_norm.x * vb_norm.x) + (va_norm.y * vb_norm.y) + (va_norm.z * vb_norm.z)

    # Error can add up here. Bound the dot_product to something we can take the acos of. Scream if it's a big delta.
    dot_product_bound = min(1.0, max(-1.0, dot_product))
    if abs(dot_product_bound - dot_product) > 0.000001:
        print(f"dot_product: {dot_product} bounded to {dot_product_bound}")

    # Return the angle.
    return degrees(acos(dot_product_bound))

def check_user_visibility(user_pos: Vector3, sat_pos: Vector3) -> bool:
    """
    Given the scenario and the proposed solution, calculate whether all users
    can see their assigned satellite.

    Returns: Success or failure.
    """

    # Get the angle, relative to the user, between the sat and the
    # center of the earth.
    angle = calculate_angle_degrees(user_pos, origin, sat_pos)

    # User terminals are unable to form beams too far off of from vertical.
    if angle <= (180.0-max_user_visible_angle):

        # Elevation is relative to horizon, so subtract 90 degrees
        # to convert from origin-user-sat angle to horizon-user-sat angle.
        elevation = str(angle - 90)
        return False

    return True

def check_self_interference(scenario: dict):
    """
    Given the scenario and the proposed solution, calculate whether any sat has
    a pair of beams with fewer than self_interference_max degrees of separation.

    Returns: Success or failure.
    """
    covered_index = 0

    for sat in scenario['sats']:
        # Get the list of beams per sat, and the sat's location.
        beams = scenario['users']
        beamslen = len(beams)-1

        keys = list(beams.keys())

        sat_loc = scenario['sats'][sat]

        # Iterate over all pairs of beams.
        i = 0
        color = 0
        count = 0
        beam_count = 1
        color_dict = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        while i < len(beams):
            j = i + 1
            while j <= len(beams):
                # Get the colors of each beam, only check for
                # self interference if they are the same color.
                # Get the locations of each user.
                user_a = beams[keys[i]]
                if j == len(beams):
                    user_b = Vector3(0,0,0)
                else:
                    user_b = beams[keys[j]]
  
                # Calculate angle the sat sees from one user to the other.
                angle = calculate_angle_degrees(sat_loc, user_a, user_b)
                if angle < self_interference_max:
                    # Exit if this pair of beams interfere.
                    count += 1
                    if count > 1:
                        color += 1
 
                    if color > 4:
                        i += 1
                        j += 1
 
                user_visibility = check_user_visibility(user_a,sat_loc)
                if user_visibility == False:
                    i += 1
                    j += 1
  
                else:
                    if color >= 4:
                        color = 0
                    interfere = check_interferer_interference(sat_loc, user_a)
                    if interfere == True:
                      print(f"sat {sat} beam {i+1} user {keys[i]}", "Interference")                    
                    else:
                        if keys[i] not in covered:
                        print(f"sat {sat} beam {beam_count} user {keys[i]} color {color_dict[color]}")
                        beam_count += 1
                        covered.append(keys[i])
                        if beam_count > beams_per_satellite:
                          beam_count = 1
                          i = len(beams)
                          j = len(beams) + 1

                    i += 1
                    j += 1

            i += 1

def main() -> int:
      """
      Entry point. Reads inputs, outputs solution.
  
      Returns: exit code.
      """
  
      # Read and store inputs. Some validation is done here.
  
      scenario = {}
      # Scenario structure:
      # scenario['sats'][sat_id] = position as a Vector3
      # scenario['users'][user_id] = position as a Vector3
      # scenario['interferers'][interferer_id] = position as a Vector3
  
      if not read_scenario(sys.argv[1], scenario):
          return -1

      result = check_self_interference(scenario)

      return 0
 

 if __name__ == "__main__":
     exit(main())

# Commented out IPython magic to ensure Python compatibility.
# %%script bash
# 
# chmod 755 solution.py
# 
# python solution.py -f input_scenario.txt > output_solution.txt
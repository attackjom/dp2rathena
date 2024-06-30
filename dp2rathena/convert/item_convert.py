# Read input data from the file
with open("input.txt", "r") as infile:
    input_data = infile.readlines()

# Process the input data
output_data = {}
for line in input_data:
    line = line.strip()  # Remove any leading/trailing whitespace
    if line:  # Ensure the line is not empty
        key, value = line.split(',')
        output_data[int(key)] = value

# Write the output data to the file in the desired format
with open("output.yml", "w") as outfile:
    for key in sorted(output_data):
        outfile.write(f"  {key}: {output_data[key]}\n")

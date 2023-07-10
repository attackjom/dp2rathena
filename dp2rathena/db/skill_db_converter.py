# Read input data from a text file
with open('skill_db.yml', 'r') as file:
    input_data = file.read()

# Splitting the input data into sections
sections = input_data.split('\n\n')

# Initializing an empty list to store the required sections
required_sections = []

# Extracting the lines with the required information for each section
for section in sections:
    section_lines = section.split('\n')
    required_lines = []

    # Extracting the lines with the desired information
    for line in section_lines:
        if line.startswith(('  Name: ', '  Description: ', '  MaxLevel: ')) or (line.endswith(':') and not(line.startswith('  '))):
            required_lines.append(line)

    # Appending the required lines for the current section to the list
    required_sections.append('\n'.join(required_lines))

# Creating the final output string
output_data = '\n\n'.join(required_sections)

# Printing the final output
print(output_data)

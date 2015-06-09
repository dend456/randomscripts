import os

map_dir = "C:\\games\\EverQuest\\maps\\"

files = ['{}\{}'.format(map_dir, f) for f in os.listdir(map_dir)]

for file in files:
    with open(file) as f:
        string = f.read()

    lines = string.split('\n')
    output = []
    for line in lines:
        if not line:
            output.append('\n')
        elif line[0] == 'L':
            columns = line.split(',')
            r, g, b = [int(x) for x in columns[-3:]]
            if r == g and r == b:
                columns[-3:] = ['0', '0', '0']
                output.append(','.join(columns))

            else:
                output.append(line)
        else:
            output.append(line)

    with open(file, 'w') as f:
        f.write('\n'.join(output))

#!/bin/env/python
import re
import sys
import math


def nCr(n,r):
    f = math.factorial
    return int(f(n) / f(r) / f(n-r))

def analyze_log():
    f = open('update_sfdata.log', 'r')
    groups_synced = []
    group_duplicates = {}
    membership_queries = 0
    connection_queries = 0
    connection_rels = 0

    group = ''
    membership_updates = 0
    for line in f:
        if line.startswith('> Group:'):
            try:
                rgx = re.search("> Group: (.+?) -- 'Membership' updates: (\d+)",
                              line)
                group = rgx.group(1)
                membership_updates = int(rgx.group(2))
                groups_synced.append(group)
            except AttributeError:
                print('ERROR at line: {0}', line)
        else:
            try:
                count = int(re.findall('\d+', line)[0])
                if 'Membership' in line:
                    membership_queries += count
                elif 'Connection' in line:
                    connection_queries += count

                    if count >= 2:
                        connection_rels += nCr(count, 2)

                    if membership_updates > 1:
                        if membership_updates != count:
                            duplicates = (membership_updates - count)
                            group_duplicates[group] = duplicates
            except:
                print('ERROR at line: {0}'.format(line))
                print("Unexpected error: {}".format(sys.exc_info()[0]))

    f.close()

    output = open('groups_synced2', 'w')
    for group in groups_synced:
        output.write(group + '\n')
    output.close()

    result = open('results2', 'w')
    result.write("> Number of 'Membership' queries: {}\n".format(membership_queries))
    result.write("> Number of 'Connection' queries: {}\n\n".format(connection_queries))

    result.write("These groups might have possible duplicate 'Membership' entries:\n\n")
    offset = 0
    for groupname, num in group_duplicates.items():
        result.write("{0}: {1}\n".format(groupname, num))
        offset += num

    result.write("\n> Number of duplicate 'Membership' entries detected: {}\n\n\n".format(offset))
    result.write(">>> NEO4J 'Membership' relationships created: {}\n".format(membership_queries - offset))
    result.write(">>> NEO4J 'Connection' relationships created: {}\n".format(connection_rels))
    result.close()



if __name__ == '__main__':
    analyze_log()

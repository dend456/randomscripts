infile = 'list.txt'
outfile = 'ranks.txt'


def write_list(list):
    with open(outfile, 'w') as f:
        f.write('\n'.join(list))


def insert_item_at_pos(item, list, start, end):
    if start == end:
        list.insert(start, item)
        return

    mid = (start + end) // 2
    choice = 0
    while choice < 1 or choice > 2:
        try:
            choice = int(input('1. {} \t2. {}: '.format(item, list[mid])))
            if choice == 1:
                insert_item_at_pos(item, list, start, mid)
            elif choice == 2:
                insert_item_at_pos(item, list, mid + 1, end)
        except ValueError:
            pass


def insert_item(item):
    with open(outfile, 'r') as f:
        list = f.read().split('\n')

    if not list[-1]:
        del list[-1]

    if item in list:
        return

    insert_item_at_pos(item, list, 0, len(list))
    write_list(list)


def main():
    with open(infile) as f:
        new_items = f.read().split('\n')

    if not new_items[-1]:
        del new_items[-1]

    with open(outfile, 'a'):
        pass

    for item in new_items:
        insert_item(item)

if __name__ == '__main__':
    main()


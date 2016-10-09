#!/usr/bin/env python
'''
Copyright 2016 John David Anderson

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: John D. Anderson
Email: jander43@vols.utk.edu
Usage: square_build.py 'integer'
Description:
    This program builds the closest approximation to a "perfect" square
    that is possible with the given integer.
'''

# libraries
import sys
import math
import random
import primefac as pf


# functions
def square_list(dimensions, item_list):
    '''
    Function to "reshape" the original list into a 2d list with the number of
    rows and cols determined from square_builder and used in square_print
    '''
    # list
    array = []

    # loop
    for item in dimensions:
        temp = []
        for i in range(item[0]):
            temp.append(item_list.pop(0))
        array.append(temp)

    # return
    return array


def square_print(row_list):
    '''
    Function to graphically print out a perfect or imperfect square based on
    build instructions from square_builder function
    '''
    # print loop
    square = ''
    for item in row_list:
        tiles = ''
        for _ in range(item[0]):
            tiles += '# '
        for _ in range(item[1]):
            tiles += '. '
        square += tiles + '\n'

    # print square
    print square


def square_builder(number):
    '''
    Function to determine how to create the "best" square (perfect or not) and
    return a list for use by square_list and square_print
    '''
    # find closest square root
    init_root = pf.introot(number, r=2)

    # find difference of root^2 and number
    diff_root = number - (init_root**2)

    # calculate rows/columns and print square
    if diff_root == 0:
        rows = init_root
        cols = init_root

        # build instruction list
        build_instr = []
        for y in range(rows):
            build_instr.append([init_root, 0])

        # print perfect square
        # print build_instr
        # square_print(build_instr)

    elif diff_root <= init_root:
        rows = init_root
        cols = init_root + 1

        # build instruction list
        build_instr = []
        for i, y in enumerate(range(rows)):
            if i + 1 <= diff_root:
                build_instr.append([init_root + 1, 0])
            else:
                build_instr.append([init_root, 1])

        # print perfect square
        # print build_instr
        # square_print(build_instr)

    else:
        rows = init_root + 1
        cols = init_root + 1

        # diff of diff
        diff = diff_root - init_root

        # build instruction list
        build_instr = []
        for i, y in enumerate(range(rows)):
            if i + 1 < rows:
                build_instr.append([init_root + 1, 0])
            else:
                build_instr.append([diff, init_root + 1 - diff])

        # print perfect square
        # print build_instr
        # square_print(build_instr)

    # return
    return build_instr

# executable
if __name__ == '__main__':

    if len(sys.argv) != 2:
        sys.exit()
    else:
        ex_list = random.sample(range(1, 1000), int(sys.argv[1]))
        print '\n{0}\n'.format(ex_list)
        list_rows = square_builder(int(sys.argv[1]))
        print '\n{0}\n'.format(list_rows)
        square_print(list_rows)
        new_list = square_list(list_rows, ex_list)
        print '\n{0}\n'.format(new_list)

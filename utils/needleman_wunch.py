#!/usr/bin/env python
import argparse
import numpy as np
import os
import sys

'''
Original code taken from:
https://gist.github.com/slowkow/06c6dba9180d013dfd82bec217d22eb5

Added comments and split up the code into functions for added readability

explanations:
https://en.wikipedia.org/wiki/Needleman%E2%80%93Wunsch_algorithm
http://experiments.mostafa.io/public/needleman-wunsch/index.html
https://berthub.eu/nwunsch/
The Needleman-Wunsch Algorithm
==============================

This is a dynamic programming algorithm for finding the optimal alignment of
two strings.

Example
-------
    >>> x = "GATTACA"
    >>> y = "GCATGCU"
    >>> print(nw(x, y))
    G-ATTACA
    GCA-TGCU

'''


def make_empty_matrix(x,y):
    return np.zeros((len(x)+1, len(y) +1))

def initialize_scores_matrix(x,y,gap):
    '''Initializes the score matrix
    this matrix will eventually contain the score for
    the score is computed by taking into account the 
    penalty (mismatch / gap) or bonus (match) you get at each pairing
    each character pair
    the first row and column are filled with numbers descending from 0
    if the gap penalty = 1 the last column cell = - len(y)-1
    and the last row cell = - len(x)-1
    0, -1, -2
    -1, 0,  0
    -2, 0,  0
    -3, 0,  0
    '''
    matrix = make_empty_matrix(x,y)
    matrix[:,0] = np.linspace(0, -len(x) * gap, len(x) + 1)
    matrix[0,:] = np.linspace(0, -len(y) * gap, len(y) + 1)
    return matrix

def initialize_path_matrix(x,y):
    '''
    Initializes a path matrix to find the cheapest path of the alignment.
    first row each cell contains 4
    first column each cell (except first) contains 3
    the numbers in the path matrix correspond to actions 
    advance x sequency or advance y sequence or advance both sequences 
    4, 4, 4
    3, 0, 0
    3, 0, 0
    3, 0, 0
    '''
    matrix = make_empty_matrix(x,y)
    matrix[:,0] = 3
    matrix[0,:] = 4
    return matrix
    
def assign_scores(x,y,F,P,match, mismatch, gap):
    '''
    assign a score to each letter combination of sequence x & y based on the
    defined scores for match, mismatch and gap
    '''
    nx, ny = len(x), len(y)
    t = np.zeros(3)
    for i in range(nx):
        for j in range(ny):
            if x[i] == y[j]:
                t[0] = F[i,j] + match
            else:
                t[0] = F[i,j] - mismatch
            t[1] = F[i,j+1] - gap
            t[2] = F[i+1,j] - gap
            # the highest score in t is the best option?
            # it considered whether the caracters matches and inserting
            # a gap for either one of the sequences
            tmax = np.max(t)
            F[i+1,j+1] = tmax
            # asign value to the path matrix
            if t[0] == tmax:
                # letters match
                P[i+1,j+1] += 2
            if t[1] == tmax:
                # letters do not match consider a gap for sequence y?
                P[i+1,j+1] += 3
            if t[2] == tmax:
                # letters do not match consider a gap for sequence x?
                P[i+1,j+1] += 4
    return F, P
    
def find_optimal_alignment(x,y,P,F=None):
    ''' 
    Trace through an optimal alignment.
    start at the bottom right and find the cheapest path to the top left

    the local best options are summed to a specific number in the
    path matrix P and based on this number the algorithm advances
    the x or y sequence (the other gets a gap -) | both sequences are 
    advanced (no gap)
    
    to provide a score you need to provide the score matrix not
    needed for best path
    '''
    i = len(x)
    j = len(y)
    rx = []
    ry = []
    score = 0
    while i > 0 or j > 0:
        if P[i,j] in [2, 5, 6, 9]:
            rx.append(x[i-1])
            ry.append(y[j-1])
            i -= 1
            j -= 1
        elif P[i,j] in [3, 5, 7, 9]:
            rx.append(x[i-1])
            ry.append('-')
            i -= 1
        elif P[i,j] in [4, 6, 7, 9]:
            rx.append('-')
            ry.append(y[j-1])
            j -= 1
        if type(F) == np.ndarray:
            score += F[i,j]
    return rx, ry, score

def nw(x, y, match = 1, mismatch = 1, gap = 1):
    ''' 
    align sequence x and y with the needleman_wunch algorithm.
    x           sequence (string)
    y           sequence (string)
    match       bonus for match characters
    mismatch    penalty for mismatching letters
    gap         penalty for using a gap (-)
    '''
    nx = len(x)
    ny = len(y)
    F = initialize_scores_matrix(x,y,gap)
    P = initialize_path_matrix(x,y)
    F, P = assign_scores(x,y,F,P, match,mismatch,gap)
    rx, ry, score = find_optimal_alignment(x,y,P,F)
    # Reverse the strings. The algorithm works backwards
    rx = ''.join(rx)[::-1]
    ry = ''.join(ry)[::-1]
    return '\n'.join([rx, ry])

def main(args):
    x = open(args.fn1).read().strip()
    y = open(args.fn2).read().strip()
    print('handling sequences stored in:',args.fn1,args.fn2)
    print('they contain',len(x),len(y), 'characters')
    match = args.match if args.match else 1
    mismatch = args.mismatch if args.mismatch else 1
    gap = args.gap if args.gap else 1
    o = nw(x, y, match = match, mismatch = mismatch, gap = gap)
    print('writing output to:',args.fn_output)
    with open(args.fn_output,'w') as fout:
        fout.write(o)
        

if __name__ == '__main__':
    p = argparse.ArgumentParser(description="align two sequences")
    p.add_argument('fn1',metavar="filename sequence 1", type=str,
        help="filename sequence 1")
    p.add_argument('fn2',metavar="filename sequence 2", type=str,
        help="filename sequence 2")
    p.add_argument('fn_output',metavar="filename output", type=str,
        help="filename output")
    p.add_argument('-match',metavar="match",type=int, required = False,
        help="match bonus value, default = 1")
    p.add_argument('-mismatch',metavar="mismatch",type=int, required = False,
        help="mismatch penalty value, default = 1")
    p.add_argument('-gap',metavar="gap",type=int, required = False,
        help="mismatch penalty value, default = 1")
    p.add_argument('--overwrite',action='store_true', required = False,
        help='whether to overwrite output file if filename already exists')
    args = p.parse_args()
    if not args.overwrite and os.path.isfile(args.fn_output):
        print(args.fn_output,'already exists doing nothing, set --overwrite')
        print('if you want to overwrite existing output file')
        sys.exit()
    if not args.fn1 or not args.fn2 or not args.fn_output:
        print('please provide filenames for sequence 1 and 2 and for output')
        sys.exit()
    main(args)
        
        
    



    

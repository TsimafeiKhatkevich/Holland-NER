#!/usr/bin/env python
from collections import defaultdict
import cgi
import sys

LABELS = ("B-LOC", "B-MISC","B-ORG","B-PER", "I-LOC", "I-MISC","I-ORG","I-PER", "O")

def print_stats(data, output):
    output.write("<table border='1'>")
    output.write("<tr>")
    output.write("<th>-</th>")
    for label in LABELS:
        output.write("<th>%s</th>" % label)
    output.write("</tr>")
    
    for row in LABELS:
        output.write("<tr>")
        output.write("<td>%s</td>" % row)

        for cell in LABELS:
            output.write("<td>%d</td>" % data[(row, cell)])
        output.write("</tr>")

    output.write("</table>")

def print_mistakes(data, output):
    output.write("<table border='1'>")
    output.write("<tr>")
    for i in ("i", "prev", "word", "next", "answer", "correct"):
        output.write("<th>%s</th>" % str(i))
    output.write("</tr>")
    
    for row in data:
        output.write("<tr>")
        for cell in row:
            output.write("<td>%s</td>" % cgi.escape(str(cell)))
        output.write("</tr>")

    output.write("</table>")


def row_cmp(a, b):
    return cmp(a[5],b[5]) or cmp(a[2], b[2]) 


def main(result_name, answer_name, test):

    with open(result_name, "r") as result_file:
        results = tuple(line.strip() for line in result_file.readlines())

    with open(answer_name, "r") as answer_file:
        answers = tuple(line.strip() for line in answer_file.readlines())

    with open(test, "r") as word_list:
        words = tuple(line.strip() for line in word_list.readlines())

    incorrect = []

    stat = defaultdict(int)

    comparison_chain = zip(results, answers)

    for i, p in enumerate(comparison_chain):
        stat[p] += 1
        if p[0] != p[1]:
            incorrect.append(tuple([i, words[i-1],words[i], words[i+1], p[0], p[1]]))

    incorrect.sort(row_cmp)


    with open("mistakes.html", "w+") as output:
        print_mistakes(incorrect, output)

    with open("table.html", "w+") as output:
        print_stats(stat, output)


if __name__ == '__main__':
    result_name = sys.argv[1]
    answer_name = sys.argv[2]
    test_name = sys.argv[3]
    main(result_name, answer_name, test_name)

def getNodeByPosit(node, posit):
    if node['posit'] == posit:
        return node

    if node['left'] is not None and getNodeByPosit(node['left'], posit) is not None:
        return getNodeByPosit(node['left'], posit)
    if node['right'] is not None and getNodeByPosit(node['right'], posit) is not None:
        return getNodeByPosit(node['right'], posit)

    return None


def nullable(node):
    if node['left'] is None and node['right'] is None:
        node['nl'] = node['key'] is None
        return node['key'] is None
    else:
        if node['key'] == '|':
            node['nl'] = nullable(node['left']) or nullable(node['right'])
            return nullable(node['left']) or nullable(node['right'])
        elif node['key'] in ['', "+"]:
            node['nl'] = nullable(node['left']) and nullable(node['right'])
            return nullable(node['left']) and nullable(node['right'])
        elif node['key'] == '*':
            node['nl'] = True
            return True
    return False  #защщщщита от зацикливания


def firstpos(node):
    if node is None:
        return
    firstpos(node['left'])
    firstpos(node['right'])

    if node['left'] is None and node['right'] is None:
        if node['key'] is None:
            node['fp'] = {}
            return {}
        else:
            node['fp'] = {node['posit']}
            return node['fp']
    else:
        if node['key'] == '|':
            node['fp'] = firstpos(node['left']).union(firstpos(node['right']))
            return node['fp']
        elif node['key'] == '':
            if nullable(node['left']):
                node['fp'] = firstpos(node['left']).union(firstpos(node['right']))
                return node['fp']
            else:
                node['fp'] = firstpos(node['left'])
                return node['fp']
        elif node['key'] in ['*','+']:
            node['fp'] = firstpos(node['left'])
            return node['fp']
    return False  # защщщщита от зацикливания


def lastpos(node):
    if node is None:
        return
    lastpos(node['left'])
    lastpos(node['right'])

    if node['left'] is None and node['right'] is None:
        if node['key'] is None:
            node['lp'] = {}
            return node['lp']
        else:
            node['lp'] = {node['posit']}
            return node['lp']
    else:
        if node['key'] == '|':
            node['lp'] = lastpos(node['left']).union(lastpos(node['right']))
            return node['lp']
        elif node['key'] == '':
            if nullable(node['right']):
                node['lp'] = lastpos(node['left']).union(lastpos(node['right']))
                return node['lp']
            else:
                node['lp'] = lastpos(node['right'])
                return node['lp']
        elif node['key'] in ['*','+']:
            node['lp'] = lastpos(node['left'])
            return node['lp']
    return False  # защщщщита от зацикливания


def followpos(node, root):
    if node is None:
        return

    if node['key'] == "":
        for i in node['left']['lp']:
            getNodeByPosit(root, i)['flp'] = getNodeByPosit(root, i)['flp'].union(node['right']['fp'])
    elif node['key'] in ['*','+']:
        for i in node['lp']:
            getNodeByPosit(root, i)['flp'] = getNodeByPosit(root, i)['flp'].union(node['fp'])

    followpos(node['left'], root)
    followpos(node['right'], root)


def tree(expression):
    stack = []
    output = []
    expression = '('+expression + ')#'
    for token in expression:
        if not output:
            output.append(token)
        elif output[-1] in ['|', '(']:
            output.append(token)
        elif token in ['|', '*', '+', ')']:
            output.append(token)
        else:
            output.append('')
            output.append(token)

    expression = []

    for token in output:
        if token in ["*", "+"]:
            expression.append(token)
        elif token == "(":
            stack.append(token)
        elif token in ["|", ""]:
            while stack and stack[-1] in ["", "*", "+"]:
                expression.append(stack.pop())
            stack.append(token)
        elif token == ")":
            while stack and stack[-1] != "(":
                expression.append(stack.pop())
            stack.pop()
        else:
            expression.append(token)

    while stack:
        expression.append(stack.pop())

    state = 1
    stack = []
    symbols = set()

    for token in expression:
        if token in ['', '|']:
            o2 = stack.pop()
            o1 = stack.pop()
            unit = dict(left=o1, right=o2, key=token, posit=None, flp={}, lp={})
            stack.append(unit)
        elif token in ['*','+']:
            o1 = stack.pop()
            unit = dict(left=o1, right=None, key=token, posit=None, flp={}, lp={})
            stack.append(unit)
        else:
            unit = dict(left=None, right=None, key=token, posit=state, flp=set(), fp={}, lp={})
            stack.append(unit)
            state += 1
            symbols.add(token)

    nullable(stack[0])
    firstpos(stack[0])
    lastpos(stack[0])
    followpos(stack[0], stack[0])

    return stack, symbols

def dfa(stack, symbols):
    Dstates = []
    Dtran = []

    #print('00000000000000000000000', stack[0])
    print(stack[0], stack[0]['right'])
    finishing = stack[0]['right']['posit']
    Dstates.append(dict(fp=firstpos(stack[0]), mark=False, finishing=(finishing in firstpos(stack[0]))))

    while True:
        S = None
        for Dstate in Dstates:
            if not Dstate['mark'] and S is None:
                S = Dstate
        if S is None:
            break
        S['mark'] = True
        for symbol in symbols:
            U = set()
            for p in S['fp']:
                node = getNodeByPosit(stack[0], p)
                if node['key'] == symbol:
                    U = node['flp'].union(U)
            flag = True
            for dstate in Dstates:
                if flag and dstate['fp'] == U:
                    flag = False

            if flag and U != set():
                Dstates.append(dict(fp=U, mark=False, finishing=(finishing in U)))
            #print(finishing, flag, U, (finishing in U))
            Dtran.append(dict(symbol=symbol, start=S['fp'], to=U))

    print('_____________________________________________________', finishing)
    ClearNat = []

    for Dtr in Dtran:
        #print('---', Dtr)
        if not Dtr['to'] == set():
            ClearNat.append(Dtr)

    return Dstates, ClearNat


def fa_gv(fa, filename):
    f = open(filename, 'w')
    f.write('digraph fa {\n')
    f.write('rankdir=LR;\n')
    f.write('node[shape=doublecircle];')
    for i in fa[4]:
        f.write('"' + str(fa[0][i]) + '";')
    f.write('\nnode[shape=circle];\n')
    for t1 in range(0, len(fa[0])):
        for a in range(0, len(fa[1])):
            for t2 in fa[2][t1][a]:
                f.write('"' + str(fa[0][t1]) +'"' + '->' + '"' + \
                    str(fa[0][t2]) + '"')
                f.write('[label="' + str(fa[1][a]) + '"];\n')
    f.write('}\n')
    f.close()


# Разворот КА
def fa_rev(fa):
    rfa = [list(fa[0]), list(fa[1]), [], list(fa[4]), list(fa[3])]
    rfa[2] = [[[] for i in range(0, len(fa[1]))] for j in range(0, len(fa[0]))]
    for t1 in range(0, len(fa[0])):
        for a in range(0, len(fa[1])):
            for t2 in fa[2][t1][a]:
                rfa[2][t2][a].append(t1)
    return rfa


# Детерминизация КА
def fa_det(fa):
    def reachable(q, l):
        t = []
        for a in range(0, len(fa[1])):
            ts = set()
            for i in q[l]:
                ts |= set(fa[2][i][a])
            if not ts:
                t.append([])
                continue
            try:
                i = q.index(ts)
            except ValueError:
                i = len(q)
                q.append(ts)
            t.append([i])
        return t
    dfa = [[], list(fa[1]), [], [0], []]
    q = [set(fa[3])]
    while len(dfa[2]) < len(q):
        dfa[2].append(reachable(q, len(dfa[2])))
    dfa[0] = range(0, len(q))
    dfa[4] = [q.index(i) for i in q if set(fa[4]) & i]
    return dfa


# Алгоритм Бржозовского
def fa_min(Dstates, ClearNat,symbols):
    fa = [None] * 5
    fa[0] = []
    fa[1] = []
    for symbol in symbols:
        if symbol != '#':
            fa[1].append(symbol)
    # fa[1] = list(symbols)
    fa[2] = []
    fa[3] = [0]
    fa[4] = []

    # fa[0] = range(len(Dstates))
    for d in range(len(Dstates)):
        # print(Dstates[d])
        fa[0].append(d)
        if Dstates[d]['finishing']:
            fa[4].append(d)

    fa[2] = []
    for q in fa[0]:
        fa[2] = fa[2] + [[]]
        fa[2][q] = []
        for a in fa[1]:
            fa[2][q] = fa[2][q] + [[]]

    for q in range(len(fa[0])):
        for a in range(len(fa[1])):
            for CNat in ClearNat:
                to = None
                for d in range(len(Dstates)):
                    if Dstates[d]['fp'] == CNat['to']:
                        to = d
                start = None
                for d in range(len(Dstates)):
                    if Dstates[d]['fp'] == CNat['start']:
                        start = d

                if CNat['symbol'] == fa[1][a] and start == fa[0][q]:
                    fa[2][q][a] = fa[2][q][a] + [to]
    #print(fa)
    fa_gv(fa, 'fa.gv')
    return fa_det(fa_rev(fa_det(fa_rev(fa))))


# MINIMIZ END
def grafviz(fa):
    fa_gv(fa_min(fa), 'fa_min.gv')
    return

# ПуНкТ ТрИ
def check(fa, chain):
    condit = 0

    try:
        for letter in chain:
            li = fa[1].index(letter)
            #print(li,'____________', fa[2][condit][li][0])
            condit = fa[2][condit][li][0]
        if condit in fa[4]:
            print('Цепочка пройдена')
            return True
        else:
            print('Цепочка пройдена не полностью')
            return False
    except:
        print('Цепочка не пройдена')
        return False


if __name__ == '__main__':
    while True:
        #expression = input("Ввод регулярного выражения: ")
        expression = '(a|b)+abb'
        #expression = '(a*|bbc)a*c*b'

        stack, symbols = tree(expression)
        Dstates, Dtrans = dfa(stack, symbols)
        fa = fa_min(Dstates, Dtrans, symbols)
        chain = input('Строка: ')
        res = check(fa, chain)
        print(res)

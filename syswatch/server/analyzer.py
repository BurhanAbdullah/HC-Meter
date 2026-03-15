def threat_score(cpu, memory, connections):

    score = 0

    if cpu > 90:
        score += 30

    if memory > 80:
        score += 20

    if connections > 200:
        score += 40

    return score

def round_to_step(value, step):
    return round(round(value / float(step)) * float(step), 10)

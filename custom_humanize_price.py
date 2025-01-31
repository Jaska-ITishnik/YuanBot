def custom_humanize(amount: str):
    if '.' in amount:
        reversed_version = amount.split('.')[0][::-1]
        return ' '.join([reversed_version[i:i + 3][::-1] for i in range(len(reversed_version)) if i % 3 == 0][::-1]) + '.' +amount.split('.')[1]
    else:
        reversed_version = amount[::-1]
        return ' '.join([reversed_version[i:i + 3][::-1] for i in range(len(reversed_version)) if i % 3 == 0][::-1])
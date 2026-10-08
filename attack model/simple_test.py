from pathlib import Path

test_file = Path(__file__).resolve().parent / 'test.txt'
with open(test_file, 'w') as f:
    f.write('test')
print('ok')

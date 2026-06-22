import  pandas as pd

path = r'c:\Users\Studio\Downloads'
name = r'\response_1780911579654.csv'
df1 = pd.read_csv(path+name)

print(df1.info)

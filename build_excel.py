import pandas as pd
import os

os.makedirs('static/downloads', exist_ok=True)
columns = [f'Col_{i}' for i in range(50)]
df = pd.DataFrame(columns=columns)

for i in range(15):
    df.loc[i] = [''] * 50

df.iloc[14, 1] = 'CEDULA'
df.iloc[14, 14] = 'APELLIDOS'
df.iloc[14, 23] = 'NOMBRES'

acronyms = ['CA', 'ILE', 'MA', 'EF', 'AP', 'CN', 'GHC', 'OC', 'PGCRP']
start_col = 30
for idx, acr in enumerate(acronyms):
    df.iloc[14, start_col + idx] = acr

df.loc[15] = [''] * 50
df.loc[15, 'Col_1'] = '31000012'
df.loc[15, 'Col_14'] = 'MENDOZA PEREZ'
df.loc[15, 'Col_23'] = 'GABRIEL'
for idx in range(len(acronyms)):
    df.loc[15, f'Col_{start_col + idx}'] = '15'

df.loc[16] = [''] * 50
df.loc[16, 'Col_1'] = '31000030'
df.loc[16, 'Col_14'] = 'HERNANDEZ RODRIGUEZ'
df.loc[16, 'Col_23'] = 'ALEXANDRA'
for idx in range(len(acronyms)):
    df.loc[16, f'Col_{start_col + idx}'] = '18.5'

df.to_excel('static/downloads/Formato_Sabana_MPPE_Ejemplo.xlsx', index=False, header=False)
print('Sabana Template created successfully')

# Generate Simple Format Template
df_simple = pd.DataFrame(columns=['CEDULA', 'APELLIDOS', 'NOMBRES', 'NOTA'])
df_simple.loc[0] = ['31000012', 'MENDOZA PEREZ', 'GABRIEL', '15']
df_simple.loc[1] = ['31000030', 'HERNANDEZ RODRIGUEZ', 'ALEXANDRA', '18.5']
df_simple.to_excel('static/downloads/Formato_Carga_Materia.xlsx', index=False)
print('Simple Template created successfully')

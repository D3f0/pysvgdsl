from dsl import SMVEFormulaManager


example_formulas = [f.strip() for f in """
    E4CVV_01.fill=SI(ai.E4CVV_01.q,6,10)
    E4CVV_01.text=str((ai.E4CVV_01.value-687)*ai.E4CVV_01.escala)
    E4CTS201.fill=SI(di.E4CTS201.value,6,3)
    E4CTS101.fill=SI(di.E4CTS101.value,6,3)
    E4CREC01.fill=SI(di.E4CREC01.value,6,3)
    E4CBAR01.stroke=SI(float(eg.E4CVV_01.text)>100,5,3)
    E4BREC01.fill=SI(di.E4BREC01.value,6,3)
    E4ABAR01.stroke=SI(eg.E4289I01.stroke=2,9,12)
    E42VV_00.fill=SI(ai.E42VV_00.q,6,10)
    E42VV_00.text=FLOAT((ai.E42VV_00.value-1227)*ai.E42VV_00.escala, 1)
""".split('\n') if f]


def main():
    fm = SMVEFormulaManager()

    for f in example_formulas:
        fm.add_formula(f)

    print(fm.context)

if __name__ == '__main__':
    main()

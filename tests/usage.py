from hdcc.HDProg import *

prog = HDProg()

prog.add_param(int, 'N', 10000)

prog.add_input(float, "x")
prog.add_output(Types.HV_FHRR, "out", 'N')

prog.decl_var(Types.HV_FHRR, "base", 10000)

for i in range(4):
    prog.decl_const(int, f"base_{i}", 10000)
prog.assign("base", prog.bind('base', 'base'))
prog.assign("out", prog.frac_bind("base", "x"))


state = prog.build()


# print(prog)

state, out = prog.run(state, {"x": 0.5})

print(out)
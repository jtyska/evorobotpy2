from gerador_ini import GeraIni


class combinador():
    def __init__(self):
        self.combinados = []
        self.lista = []

    def todasCombina(self, lista_params, dicionario, n=0):
        if n == 0:
            self.lista = []
        if n == len(lista_params):
            return
        else:
            for x in dicionario[lista[n]]:
                self.lista.append(x)
                if n == len(lista_params)-1:
                    self.combinados.append(self.lista.copy())

                self.todasCombina(lista_params, dicionario, n+1)
                self.lista.pop()

    def combinados_to_dict(self, lista_params):
        new_dic = {}
        new_list = []
        for lista in self.combinados:
            for x in range(len(lista_params)):
                new_dic[lista_params[x]] = lista[x]

            new_list.append(new_dic.copy())
        self.combinados = new_list


if __name__ == '__main__':
    d = combinador()


    name = 'envVarInvestigation'
    base = {
       'enviroment': ['HopperBulletEnv-v0','AntBulletEnv-v0','HalfCheetahBulletEnv-v0','Walker2DBulletEnv-v0','HumanoidBulletEnv-v0'],
       'percentual_env_var': [0, 0.3, 0.5, 1.0, 1.5,3.0], 
       'action_noise': [0, 1]
    }

    lista = list(base.keys())

    bat = d.todasCombina(lista, base)
    print(d.combinados)
    d.combinados_to_dict(lista)
# print(d.combinados)

    gerador = GeraIni(d.combinados)
    gerador.criar_all_exp()

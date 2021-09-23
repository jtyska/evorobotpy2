import json
import os
name = 'envVarInvestigation'
base = {'enviroment': ['HopperBulletEnv-v0','AntBulletEnv-v0','HalfCheetahBulletEnv-v0','Walker2DBulletEnv-v0','HumanoidBulletEnv-v0'],
        'percentual_env_var': [0, 0.3, 0.5, 1.0, 1.5,3.0], 'action_noise': [0, 1]}


class GeraIni():
    def __init__(self, dic_list):
        self.__dic_list = dic_list

        self.filename = 'ini_tudo.json'

        self.dir = os.listdir()

    def search_exp(self, dic):
        with open(self.filename) as data:
            self.__ini_data = json.load(data)

        while True:
            encontrado = self.procura_exp(dic)
            if encontrado:
                break
            self.exp = input("your experiment don't exists")
            self.exp = self.exp.strip()

    def procura_exp(self, dic):
        for exp in self.__ini_data:
            if dic['enviroment'] in exp.keys():
                self.__ini_data = exp
                print(self.__ini_data)
                return True
        return False

    def modificar_dict_old(self, N=0):

        data = self.__ini_data[self.exp]
        for values in data.items():
            values = values[1]
            for key in self.__entrada:
                if key in values:
                    values[key] = self.__entrada[key][N]
        self.ini_feito = data
        return data

    def modificar_dic(self, dic):
        data = self.__ini_data[dic['enviroment']]
        for values in data.items():
            values = values[1]
            for key in dic:
                if key in values:
                    values[key] = dic[key]
        self.ini_feito = data
        return data

    def gerar_ini_Lista(self, lista_dic):
        pass

    def criar_dir(self, Name, N=0):
        self.dir = os.listdir()
        Nome = Name + '-' + str(N)
        if Nome in self.dir:
            return self.criar_dir(Name, N+1)
        else:
            os.mkdir(Nome)
            return Nome

    def criar_N_ini(self, N):
        os.mkdir(self.__nome)
        for x in range(N):
            self.ini_feito = self.modificar_dict(x)
            nome = self.criar_ini(x)
            self.criar_txt(nome)

    def criar_ini(self, dic):
        exp = dic['enviroment']
        pasta = self.criar_dir(exp)
        nome_ini = pasta + f'.ini'
        path = os.path.join(pasta, nome_ini)

        with open(path, 'w') as inifile:
            inifile.write('[EXP]\n')
            inifile.write('environment ='+exp+str('\n'))
            for key, args in self.ini_feito.items():
                inifile.write(key+"\n")
                for skey, sargs in args.items():
                    linha = skey+" = "+str(sargs)+"\n"
                    inifile.write(linha)
            self.criar_txt(pasta, nome_ini)
        return nome_ini

    def criar_txt(self, pasta, nome):
        txt = open('ini_list.txt', 'a')

        txt.write(f'{pasta},{nome},\n')

        txt.close()

    def criar_exp(self):
        self.modificar_dict()
        self.criar_ini()

    def criar_all_exp(self):
        for x in self.__dic_list:
            self.search_exp(x)
            self.modificar_dic(x)
            self.criar_ini(x)


if __name__ == '__main__':
    arquivo = GeraIni()

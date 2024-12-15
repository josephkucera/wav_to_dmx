# from helloworld import*
# greeding = 'Hello world!'   # comment, ctrl + /
#                             #, Python neignoruje prázdná místa na řádku
# print (greeding)
# a = 4
# b = 1 / 2

# # operátory +, -, / děleno, // děleno bez desitiných míst, % zbytek po dělení, ** mocnina, == je rovno?, =! není rovno
# # Zkratky 
# #   ctrl D, vybere další proměnnou se stejným jménem jako označená
# # přiřazení proměnné na tvrdo a = str('be')
# print("") # prazdna lajna
# c = a ** b
# print(c)

# c = a % b
# print(c)

# print("")

# if a > b:
#     print('Je cerstva')
# else:
#     print('neni cerstva')

# # vytištění symbolu před symbol dáme \ Pro vytištění nového řádku \n
# print('I\'am')

# d = 1
# while d <= 5:
#     print (d)
#     d +=1
    
names = ["robert", "kocka", "pes"] # vytiskne postupne kazde jmeno
for x in names:
    print (x)
slovo = "ahojokrujecky" 
for x in slovo: #vytiskne kazde pismeno
    print (x)
# break klasicky stopne loop, continue přeskočí aktuální iteraci ale bude pokračovat dál v loopu
for x in range(1,5):
    print(x)

# print("")
# for x in range (0,10,2): # (od, do, krok)
#     print(x)


# helloworld()
sum(2,4)
# navrat = returning (1,2)
# print(navrat)


print ("\n")

class Auticko:
    def __init__(self, vyroba, model):
        self.vyroba = vyroba
        self.model = model
        
    def jede(self):
        print ('\njede zlevadoprava\n')
        
    def get_info (self):
        print(f"\nVyrobce {self.vyroba}, model {self.model}. ")
        
        
moje_auto = Auticko('skodovka', 'oktavka')

print(moje_auto.model)
print(moje_auto.vyroba)
moje_auto.jede()
moje_auto.get_info()

tvoje_auto = Auticko('Od popelnic','sunka')
tvoje_auto.get_info()
tvoje_auto.jede()

class letadlo(Auticko):
    def __init__(self, vyroba, model,let):
        super().__init__(self,vyroba,model)
        self.let = let
        
    def jede(self):
        print('leta nahoru dolu')

moje_letadlo = letadlo('cesna','spitfire','B-2548')
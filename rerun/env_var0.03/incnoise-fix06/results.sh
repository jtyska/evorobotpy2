cd xhopper
python ../bin/plotave.py > ../results.txt
cat S*.fit
cd ../xhalfcheetah
python ../bin/plotave.py >> ../results.txt
cat S*.fit
cd ../xant
python ../bin/plotave.py >> ../results.txt
cat S*.fit
cd ../xwalker
python ../bin/plotave.py >> ../results.txt
cat S*.fit
cd ../xhumanoid
python ../bin/plotave.py >> ../results.txt
cat S*.fit
cd ..
cat results.txt

cd xhopperv0
python ../bin/plotave.py > ../resultsv0.txt
cat S*.fit
cd ../xhalfcheetahv0
python ../bin/plotave.py >> ../resultsv0.txt
cat S*.fit
cd ../xantv0
python ../bin/plotave.py >> ../resultsv0.txt
cat S*.fit
cd ../xwalkerv0
python ../bin/plotave.py >> ../resultsv0.txt
cat S*.fit
cd ../xhumanoidv0
python ../bin/plotave.py >> ../resultsv0.txt
cat S*.fit
cd ..
cat resultsv0.txt

# neural-art-transfer

# link to the wesbite
https://neural-artwork-transfer.herokuapp.com/




in order to use the app 

1 - install packages from requirements.txt

2 - install redis to your machine (used for running functions asynchronously)

  - if you are on a mac you can brew install redis 
  
3 - using terminal or command line type: redis-server 
  
4 - cd into this folder in terminal and type: python worker.py 
  
    - this will stat asynchronous worker to process functions when ready on your local machine 
    
5 - run flask 

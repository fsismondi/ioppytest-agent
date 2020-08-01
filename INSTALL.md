Installation
------------

### OS Requirements

- [OS requirement] agent component runs on MacOs (tested with MacOs 10.12.x) and debian-based distributions
- [OS requirement] for MacOs, `tuntap` driver is needed: `brew install Caskroom/cask/tuntap`
- [python version] python 2.7 needed (virtualenv use is recommended)

---------------------------------------------------------------------------------

(!) Agent runs only on python2

---------------------------------------------------------------------------------

(!) Windows is for the time being not supported by the agent. \n
If your implementation can run into a virtual machine or docker container please\n
setup that environment so yo can run the agent from within.\n

----------------------------------------------------------------------------------


### Please install the agent using PyPi (python script):

#### OPTION 1: using virtual env (recommended):

```

# install venv
>>> pip install virtualenv 

# create a python 2.7 env
>>> virtualenv -p /usr/bin/python2.7 my_venv 

# activate env
>>> source my_venv/bin/activate

# install package
>>> pip install ioppytest-agent 

```


#### OPTION 2: (without virtualenv):

```
# install package
>>> python2.7 -m pip install ioppytest-agent
```

------------------------------------------------------------------------------


#### OPTION 3: No install.
 
You can execute directly from source code, for this use, and check out README.md:

```
>>> git clone https://github.com/fsismondi/ioppytest-agent.git
>>> cd ioppytest-agent
>>> python2.7 -m pip install -r requirements.txt
>>> python2.7 setup.py develop
>>> ioppytest-agent --help
```

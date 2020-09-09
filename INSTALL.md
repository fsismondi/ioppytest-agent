Installation
------------

# OS Requirements

- [OS requirement] agent component runs on MacOs (tested with MacOs 10.12.x) and debian-based distributions
- [OS requirement] for MacOs, `tuntap` driver is needed: `brew install Caskroom/cask/tuntap`
- [python version] python 2.7 needed (virtualenv use is recommended)

(!) Agent runs only on python2
(!) Windows is for the time being not supported by the agent.

If your implementation can run into a debian-like os but you don't own one, please use a virtual machine 
or run it from within a docker container.

# Installing the agent:

## Option 1: using virtual env (recommended):

```

# install venv
>>> pip install virtualenv 

# create a python 2.7 env
>>> virtualenv -p /usr/bin/python2.7 my_venv 

# activate env
>>> source my_venv/bin/activate

# install package
>>> pip install ioppytest-agent 

# test install
>>> ioppytest-agent --help
```


## Option 2: (without virtualenv):

```
# install package
>>> python2.7 -m pip install ioppytest-agent

# test install
>>> ioppytest-agent --help
```

## Option 3: Run it from the source code"
 
```
>>> git clone https://github.com/fsismondi/ioppytest-agent.git
>>> cd ioppytest-agent
>>> python2.7 -m pip install -r requirements.txt
>>> python2.7 setup.py develop

# test install
>>> ioppytest-agent --help
```

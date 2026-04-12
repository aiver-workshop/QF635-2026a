# QF635: Market Microstructure & Algorithmic Trading
> ⚠️ This repository is strictly for educational purposes only.
> It does not constitute financial advice or endorsement of any trading exchanges or platforms.
---


## 🛠 Required Software
This course requires the following free tools:
  1. Anaconda - Python environment & package management
  2. PyCharm - Python IDE
  3. Git - Version control & repository download

## 🐍 Anaconda - Setting up a Python environment

Download and install Anaconda from https://www.anaconda.com/. 

Select all the checkboxes during the installation steps.

After installation, open `Anaconda Powershell Prompt` to create a Python 3.11 environment with the name `py311-smu2026` by typing:
```
conda create -n py311-smu2026 python=3.11
```
Multiple environments of different Python version can be created for other projects. To see the list of Anaconda environments and the installation directory:

```
conda info --envs
```
Each environment installation directory contains the `python.exe`, and we will need this path for configuring PyCharm later. Go to the directory to explore more.

We are going to install more libraries under `py311-smu2026` environment. First activate it:

```
conda activate py311-smu2026
```
To check Python version, enter the following:
```
python --version
```

To speed up installation of some libraries, use Mamba, which is a specialized version of Conda written in C++ for maximum speed. Install it once:
```
conda install -c conda-forge mamba
```

Next install the project's dependency with the following libraries (sometimes called packages):
```
mamba install numpy
mamba install matplotlib
mamba install python-gnupg
mamba install requests
mamba install python-dotenv
mamba install websockets
mamba install pandas-ta
mamba install schedule
mamba install python-binance
mamba install yfinance
python -m pip install tradingview-screener
```
`-c` stands for --channel. It is used to specify a channel where to search for the package, and the channel is often the named owner.

To get the list of packages installed:
```
> conda list
```

## 🧑‍💻 Github - Download the course repository (Python codes)
Download and install Git from https://git-scm.com/downloads

Course repository is hosted on GitHub: https://github.com/aiver-workshop/qf635

We are going to download course repository to folder on our PC, for example under `~/smu` (`~/` refers to home folder)

Open `Git Bash` and enter the followings:
```
$ cd ~
$ mkdir smu
$ cd smu
$ git clone https://github.com/aiver-workshop/QF635-2026.git

```
These steps will download course repository in a folder (for example `~/smu/QF635-2026`), and this is going to be our `working directory`.



## 💻 PyCharm - Integrated Development Environment (IDE)
Download and install PyCharm (Community version) from https://www.jetbrains.com/pycharm/

After completing the installation, setup course project in PyCharm by:
1. Open the code repository by `File` -> `Open...` -> select/navigate to `working directory`
2. Configure the Python interpreter by `File` -> `Settings...` -> `Project: QF635-2026` -> `Python Interpreter` -> `Add Interpreter` -> `Add Local Interpreter` -> `Conda Environment` -> `Use Existing environment` -> `py311-smu2026`

Lower-right side of the screen should show `py311-smu2026`

By default, the new user interface (UI) is a new redesigned look of PyCharm. Optionally, revert to Classic UI by `File` -> `Settings...` -> `Appearance & Behavior` -> `New UI` -> unselect `New UI`

## ▶️ Run your first script
Go to the `welcome` folder, double click on `hello.py` to open the script in editor, then right click on it and `Run 'hello'`. The script should run without error and produce a similar output as follows:
```
Welcome to QF635: Market Microstructure & Algorithmic Trading
         *
        ***
       *****
      *******
     *********
    ***********
   *************
  ***************
 *****************
*******************
         |
         
Process finished with exit code 0

```

🚀 You're Ready!
You are now set up to begin the course and start building algorithmic trading strategies.

## Binance Testnet
A testnet is a simulated trading environment that replicates the functionality of a real exchange, but without using actual cryptocurrencies. It allows you to safely test the Balance Bot and experiment with different rebalancing strategies without any financial risk.

Visit https://www.binance.com/en/academy/glossary/testnet and register for a standard trading account.

Once logged in, navigate to `Trade` → `Demo Trading` to switch to the testnet environment.

Create your API credentials by going to `API Management`, generating a new API key, and ensuring it is configured for demo trading use:
1. Hover over your profile icon (top right corner)
2. Click on `Demo Trading API` from the dropdown menu
3. `Create API` -> `System generated`

> ⚠️ **Important:**  
> - Make sure to **save both your API Key and Secret Key securely**  
> - The **Secret Key is only displayed once** upon creation and cannot be retrieved again later  
> - If you lose the Secret Key, you will need to delete the API and create a new one

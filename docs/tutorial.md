
# Introduction
first, of course, install the shizzle


# The GUI's
There are two main graphical user interfaces (GUI). One for tweaking the model parameters (Model GUI) and one for manage the input data (Data GUI).
## Model GUI

First, open an input file. 

(1) display's the actors available in the dataset. 

(2) display's the available issues. 

(3) display's the different parameters for the model.

(4) summaries the current settings 

### Parameters

#### Salience weight
Never used
#### Fixed weight 
Never used 

#### P-values
With this set of inputs the variation of p can be tweaked. 

start=0 step=0.05 stop=0.5 gives a sequence of 0.00, 0.05, 0.10, 0.15 ... 0.50   
##### Start
The first p-value 
##### Step size
The the incremental amount for p for each step 
##### Stop
The last p-value to included 

#### Iterations
The amount of negotiation rounds. 10 iterations will involve 10 connected rounds of negotiation where in each round the actor shifts from his original position. 
#### Repetitions 
The amount of model repetitions. Needed to ensure statistical significance. 

### Menu's
#### Open
#### Output
Different output types

- sql
- csv 
- summary 

## Data GUI
The data GUI is designed for easy creation and manipulation of the data

There are three components 

- Actors
- Issues
- Actor issues

Robert Thompson has written an excellent instruction to determine these values for real world research. `link to pdf`. 

### Actor
An actor has a name and a **power**. The **power** is used to set each **Actor Issue**

### Issue
An Issue has a name and a lower & upper bound. You can leave the lower & upper bound to 0 to discard the values and let the model dynamically determine the lower and upper bound through the given values of the actor.


### Actor Issue 
The position of each actor on each issue is defined by an Actor Issue. The position of an actor on an issue is based on the position of the other actors. The salience for an actor depends relatively on the other issues for an actor.   
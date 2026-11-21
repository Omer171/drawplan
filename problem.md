# Problem

Often when learning to draw a person will find the task of getting to a proficient stage
to be daunting and almost insurmountable. The goal at the end will seem so far and distant
while each step to get there is so small and insignificant a learner will feel as if they
are not improving at all. "Being good at art" is also a very vague and subjective thing,
and what one needs to do to become "good" is also unclear. That is why keeping track of
what you have done is so important, cause it is the only way to actually see and visualize
your improvement.

# Initial requirements

* R1. The program asks the user for an art goal (potraits, figure, anatomy, manga, comic,
animation) and the program saves it.
* R2. The program takes in this art goal and creates a visually clear guideline/roadmap for
the user. If the goal includes several skills (example the user wants to learn how to draw
manga. skills needed; panelling, anatomy, penning, inking, etc) create a progress bar for
each skill. Also it should have major roadmarkers for acheiving specfic tasks (ie. studying
for a total of 100 hours, drawing 100 figure, etc.). It should feel like a game.
* R3. The program should everyday give the user a specific task to do for that day.
* R4. The program should than upon recieving what the user actually did for the day, adjust
for the user actually did. Ask the user for how long they studied, what they ended up
actually working on and how long they spent on the goal.

# Round 2 Requirements

* R5. The program should let the user save the art they made for the day by giving it the file path to the image, and it saves it with the date and which skill it was for. Every month the program should open a old piece next to a recent one for the same skill so the user can actually see there improvement, since thats the whole point of tracking it.
* R6. To make it actually feel like a game the user should earn xp for every hour studied and every task completed, level up each skill separately (ex. anatomy lvl 4, panelling lvl 2), and have a streak for how many days in a row they drew. Hitting one of the major roadmarkers from R2 should give a big xp bonus.

# Round 3 Requirements

* R7. At the end of every week the program should give the user a summary of what they did, total hours, hours per skill, and tasks completed vs skipped. It should also find which skill the user has been neglecting the most and make the daily tasks from R3 focus more on that skill the next week.
* R3 (changed in round 3). The program should everyday give the user a specific task to do for that day. The task should normally rotate between all the skills in the users goal, but if the weekly summary from R7 found a skill the user has been neglecting, than the tasks for the next week should focus more on that skill (ex. 3 or 4 days out of the 7) until it catches up with the others.            	     Whats changed:  originally R3 would only give you one task, but now it rotates the task based on all the skills you are learning, and neglected tasks get more days in the week to focus on them.




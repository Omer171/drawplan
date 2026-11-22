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

# Round 4 Requirements

* R8. When a skill reaches 100% of its target it should count as mastered. A mastered skill gets taken out of the normal task rotation and cant be flagged as neglected anymore, but every couple weeks the program should still give a small review task for it so the user doesnt lose it. The user should also be able to set a different hour target for each skill (ex. anatomy 50 hours, inking 15 hours) instead of every skill being 20 hours, and the user can raise a target after mastering it if they want to keep going.
* R9. The user should be able to edit or delete a log or a saved art piece from inside the program, instead of having to go into the json file. When the program starts it should check that every saved art image still exists, and if one is missing it tells the user and asks if they want to remove that entry.

# Round 5 Requirements

* R10. If the user logs practice on a day without asking for the task, that day should count as "free practice" and not as skipped. The user should also be able to mark 1 rest day a week ahead of time. A rest day doesnt count as skipped and doesnt break the streak, so taking a planned day off doesnt feel like failing.

# Round 6 Requirements

* R11. After the user logs what they did for the day, the program should ask them to write one thing that went well and one thing they want to fix (ex. "hands looked stiff", "panels felt too crowded"), and save it with the skill they worked on. The next time the program gives a task for that skill, it should show the user there last "fix" note so they know what to focus on, and once a month the user can look back at all there notes for a skill to see which problems they actually fixed and which ones keep coming back.


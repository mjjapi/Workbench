#!/usr/bin/env python2.7

import colorconsole
from colorconsole import terminal
import time
import sys
from select import select
import logging as mylog
import os
from datetime import datetime
from random import randint

class KittyBox():

    def __init__(self, kitty_time, resize):
        self.kitty_time = kitty_time 
        self.pStartX = 1
        self.pStartY = 1
        ##  Set kitty terminal size to just that of kitty box ##
        self.resize = resize
        if resize:
            self.rows = size[0]
            self.columns = size[1]
            print "\x1b[8;17;26t"
            

    ## For kitty art reference ##
    def draw_kitty_R(self):
        print "     .     .         "
        print "     |\.-./|         "
        print "    /       \        "
        print "   /  /\ /\  \    __ "
        print "   \==  Y  ==/   /  )"
        print "    ;-._^_.-;   /  / "
        print "   /   \_/   \ /  /  "
        print "   |   (_)   |/  /   "
        print "  /|  |   |  |\ /    "
        print " | |  |   |  | |     "
        print "  \|  |___|  | /     "
        print('   \'\"\"\'   \'\"\"\'       ')
        return True

    def draw_kitty_purr_L(self):
        print "     .     .         "
        print "     |\.-./| ~purr~  "
        print "    /       \        "
        print "   /  /\ /\  \  _    "
        print "   \==  Y  ==/ ( \   "
        print "    ;-._^_.-;   ) )  "
        print "   /   \_/   \ /  /  "
        print "   |   (_)   |/  /   "
        print "  /|  |   |  |\ /    "
        print " | '""'   |  | |     "
        print "  \_  ;___|  |/      "
        print('    \"\"    \'\"\"\'       ')

    def draw_kitty_purr_R(self):
        print "     .     .         "
        print "     |\.-./|         "
        print "    /       \ ~purr~ "
        print "   /  /\ /\  \  _    "
        print "   \==  Y  ==/ ( \   "
        print "    ;-._^_.-;   ) )  "
        print "   /   \_/   \ /  /  "
        print "   |   (_)   |/  /   "
        print "  /|  |   |  |\ /    "
        print " | |  |   '""' |     "
        print "  \|  |___;  _/      "
        print('   \'\"\"\'    \"\"        ')

    def draw_kitty_L(self):
        print "     .     .         "
        print "     |\.-./|         "
        print "    /       \        "
        print "   /  /\ /\  \  _    "
        print "   \==  Y  ==/ ( \   "
        print "    ;-._^_.-;   ) )  "
        print "   /   \_/   \ /  /  "
        print "   |   (_)   |/  /   "
        print "  /|  |   |  |\ /    "
        print " | |  |   |  | |     "
        print "  \|  |___|  |/      "
        print('   \'\"\"\'   \'\"\"\'       ')
        return True

    ## Load kitty art lines into a kitty lines list ##
    def kitty_art(self, tail, meow, purr):
        mylog.debug('Loading kitty art into kitty list')
        mylog.debug('Current purr state is %s' % purr)
        mylog.debug('Current meow state is %s' % meow)
        kitty_lines = []
        line_1 = "      .     ."
        kitty_lines.append(line_1)
        if meow:
            line_2 = "      |\.-./|  MEOW!"
            line_3 = "     / ^   ^ \ "
        else:
            line_2 = "      |\.-./|"
            line_3 = "     /       \ "
        if purr == 'left':
            line_2 = "      |\.-./| ~purr~"
        if purr == 'right':
            line_3 = "     /       \ ~purr~"
        kitty_lines.append(line_2)
        kitty_lines.append(line_3)
        if tail == "left":
            if meow:
                line_4 = "    /==  Y  ==\  _"
                line_5 = "    \    0    / ( \ "
                line_6 = "     ;-._ _.-;   ) )"
            else:
                line_4 = "    /  /\ /\  \  _"
                line_5 = "    \==  Y  ==/ ( \ "
                line_6 = "     ;-._^_.-;   ) )"
        else:
            if meow:
                line_4 = "    /==  Y  ==\    __"
                line_5 = "    \    0    /   /  ) "
                line_6 = "     ;-._ _.-;   /  /"
            else:
                line_4 = "    /  /\ /\  \    __"
                line_5 = "    \==  Y  ==/   /  ) "
                line_6 = "     ;-._^_.-;   /  /"
        kitty_lines.append(line_4)
        kitty_lines.append(line_5)
        kitty_lines.append(line_6)
        line_7 = "    /   \_/   \ /  /"
        kitty_lines.append(line_7)
        line_8 = "    |   (_)   |/  /"
        kitty_lines.append(line_8)
        line_9 = "   /|  |   |  |\ /"
        kitty_lines.append(line_9)
        if purr == 'left':
            line_10 = "  | \'\"\"\'   |  | |"
            line_11 = "   \_  ;___|  |/"
            line_12 = ('     \"\"    \'\"\"\'')
        if purr == 'right':
            line_10 = "  | |  |   \'\"\"\' |"
            line_11 = "   \|  |___;  _/"
            line_12 = ('    \'\"\"\'    \"\"')
        if not purr:
            line_10 = "  | |  |   |  | |"
            line_11 = "   \|  |___|  |/"
            line_12 = ('    \'\"\"\'   \'\"\"\'')
        kitty_lines.append(line_10)
        kitty_lines.append(line_11)
        kitty_lines.append(line_12)
        mylog.debug('Kitty list is %s' % kitty_lines)
        return kitty_lines 

    ## Draw the kitty ##
    def draw_kitty(self, screen, kitty_lines):
        mylog.debug('Drawing kitty')
        current_line = 1
        for line in kitty_lines:
            screen.gotoXY(self.pStartX + 1, self.pStartY + current_line)
            print line
            mylog.debug('Drew line %s' % line)
            current_line += 1
        return True

    ## Draw the kitty box ##
    def draw_box(self, screen):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mylog.debug('Drawing the kitty box')
        current_line = 0
        cell_height = 12
        cell_width = 25
        screen.gotoXY(self.pStartX, self.pStartY)
        print '+' + '-' * (cell_width -2 ) + '+'
        for i in range (cell_height):
            current_line += 1
            screen.gotoXY(self.pStartX, self.pStartY + current_line)
            print '|' + ' ' * (cell_width - 2) + '|'
        ## Imput time/calendar and border ##
        print '+' + '-' * (cell_width -2 ) + '+'
        print '+' + '- ' + current_time + ' -+'
        print '+' + '-' * (cell_width -2 ) + '+'
        mylog.debug('Kitty box drawn')
        return True

    ## For random cute ##
    def random_cute(self, kitty_time_left):
        mylog.debug("Time left for kitty is %s" % kitty_time_left)
        cute_time = randint(120,240)
        cuteness = self.cute_pick()
        mylog.debug("Next random cute in %s seconds!" % cute_time)
        return cute_time, cuteness
    def cute_pick(self):
        random_pick = randint(0,1000)
        if random_pick % 2 == 0:
            cuteness = 'purr'
        else:
            cuteness = 'meow'
        return cuteness

    ## Run the kitty script! ##
    def Execute(self):
        mylog.debug('Kitty will hang out for %s seconds' % self.kitty_time)
        screen = terminal.get_terminal()
        screen.clear()
        screen.set_title("=^..^=")
        tail = 'left'
        purr_time = False
        meow = False
        cute_time, cuteness = self.random_cute(self.kitty_time)
        cute_count = 1 
        purr = None
        while self.kitty_time > 0:
            mylog.debug('Setting kitty screen parameters')
            mylog.debug('Kitty tail is %s' % tail)
            mylog.debug('Countdown to next cute time is %s seconds!' % (cute_time - cute_count))
            ## Are we gonna do sumthin' cute? ##
            rlist, _, _ = select([sys.stdin], [], [], 1)
            if rlist: 
                cute_check = sys.stdin.readline()
                if cute_check:
                    cuteness = self.cute_pick() 
            if cute_count == cute_time:
                cute_time, cuteness = self.random_cute(self.kitty_time)
                cute_count = 0 
            if cuteness == 'meow':
                meow = True
            if cuteness == 'purr':
                purr_time = True
            ## Gather kitty parameters and draw that kitty ##
            if purr_time:
                purr = 'left'
                self.draw_box(screen)
                kitty = self.kitty_art(tail, meow, purr)
                self.draw_kitty(screen, kitty)
                time.sleep(1)
                purr = 'right'
                self.draw_box(screen)
                kitty = self.kitty_art(tail, meow, purr)
                self.draw_kitty(screen, kitty)
            else:
                self.draw_box(screen)
                kitty = self.kitty_art(tail, meow, purr)
                self.draw_kitty(screen, kitty)
            if tail == 'left':
                tail = 'right'
                mylog.debug('Changed tail to %s' % tail)
            else:
                tail = 'left'
                mylog.debug('Changed tail to %s' % tail)
            ## Reset and adjust counters for the next kitty iteration ##
            current_line = 1
            self.kitty_time -= 1
            cute_count += 1
            meow = False
            purr_time = False
            purr = None
            cuteness = None
        screen.clear()
        ##  Return screen to previous sizesize ##
        if self.resize:
            print("\x1b[8;%s;%st" % (self.rows, self.columns))
        print "Kitty naptime!  Please come again!!"

## Input the kitty parameters ##
if __name__ == '__main__':
    import argparse
    #Parse command line arguments
    parser = argparse.ArgumentParser(add_help=True, description='Hang out with a virtual kitty!! Press <Enter> to make them do something cute!')
    parser.add_argument("-k", "--kitty_time", action="store", dest="kitty_time", default=None, help="how long the kitty will chill with you (in seconds)")
    parser.add_argument("-r", "--resize", action="store_true", dest="resize", default=False, help="if you wish to resize your window to fit only the kitty")
    parser.add_argument("--debug", action="store_true", dest="debug", default=False, help="display kitty debug messages")

    args = parser.parse_args()
    debug = args.debug

    if debug:
        mylog.basicConfig(stream=sys.stdout, level=mylog.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    else: mylog.basicConfig(stream=sys.stdout, level=mylog.INFO, format='%(asctime)s %(levelname)s - %(message)s')
    
    if not args.kitty_time:
        print "But.. really.. how long do you want the kitty to hang out (in seconds)?"
        print "Use the -k option for kitty time!!"
        sys.exit(1)
    else:
        args.kitty_time = int(args.kitty_time)
    if args.resize:
        size = []
        rows, columns = os.popen('stty size', 'r').read().split()
        size.append(rows)
        size.append(columns)
    else:
        size = None

    KittyTime = KittyBox(args.kitty_time, size)
    try:
        KittyTime.Execute()
    except SystemExit:
        if args.resize:
            print("\x1b[8;%s;%st" % (rows, columns))
        raise
    except KeyboardInterrupt:
        if args.resize:
            print("\x1b[8;%s;%st" % (rows, columns))
        print "Ok, we'll put kitty away"
        sys.exit(1)
    except:
        if args.resize:
            print("\x1b[8;%s;%st" % (rows, columns))
        print "Ermm.. that's weird.  Kitty's confuseded."
        raise
        sys.exit(1)

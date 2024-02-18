#!/usr/bin/python2
# encoding: utf-8

def format_timestring(timelist):
	timeint = 0
	for i in timelist: #convert given time to float
		try:
			num=int(i[:-1]) #the number part
			if i[-1]=='d':
				timeint+=num*3600*24
			elif i[-1]=='h':
				timeint+=num*3600
			elif i[-1]=='m':
				timeint+=num*60
			elif i[-1]=='s':
				timeint+=num
			else:
				raise Exception("doh!")
		except:
			raise Exception("Bad argument @ \"{0}\", format is: 1h 2m 3s".format(i))
	return timeint

def split_large_message(text, delimiter="\n", charlimit=1999):
	templist = text.split(delimiter)
	tempstr = ""
	result = []
	print(templist)
	for i in range(0,len(templist)):
		tempstr += templist[i]
		msglen = len(tempstr)
		if msglen >= charlimit:
			raise("Text split failed!")
		elif i+1 < len(templist):
			tempstr += delimiter
			if msglen+len(templist[i+1]) >= charlimit-2:
				result.append(tempstr)
				tempstr = ""
		else:
			result.append(tempstr)
	return result

ranks = {
	2000: " 〈★〉",
	1950: "〈A+〉",
	1900: "〈A〉",
	1850: "〈A-〉",
	1800: "〈B+〉",
	1750: "〈B〉",
	1700: "〈B-〉",
	1650: "〈C+〉",
	1600: "〈C〉",
	1550: "〈C-〉",
	1500: "〈D+〉",
	1450: "〈D-〉",
	1400: "〈E+〉",
	1350: "〈E〉",
	1300: "〈E-〉",
	1200: "〈F+〉",
	1100: "〈F〉",
	1000: "〈F-〉",
	0: "〈G〉"}

def rating_to_icon(rating):
	for i in sorted(ranks.keys(), reverse=True):
		if rating >= i:
			return(ranks[i])

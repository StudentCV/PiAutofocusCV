#Written by Raoul Nottrott, Project Autofocus, Basler AG 2015
#This module provides some peak finding algorithms

import time
import sys
import cv2
from focus_measures import ContrastMeasures
		
def fibonacci_peak(cam,focus,ak,bk,aoi,hysteresis,tolerance):
  """Fibonacci peak search taken from E. Krotkov: "Focusing" P.233"""
  #	cam: camera already opened
  #	focus: focus from used LenseController
  #	ak: start step no.
  #	bk: stop step no.
  #	aoi: area of interest in form [x1,y1,x2,y2]
  #	hysteresis: offset to compensate hysteresis
  #	tolerance: tolerance limit, algorithm stops when the search interval becomes smaller than tolerance
  
  which=0
  N=fibonacci(bk)[1]	#calculate theoretical number of loops needed for peak finding
  nCount=0			#variable to count actual number of loops used
  dir=1				#indicates lense's step direction, 1: step forward, 0: step backward
  					#(needed to compensate lense hysteresis depending on move direction)
  goto=0				#saves last position to detect move direction
  offset=0			#offset to add to actual position to compensate hysteresis, offset is 
  					#either =hysteresis or 0-1*hysteresis depending on step direction
  fm = ContrastMeasures()
  for k in range(1,N+1):
  	nCount+=1		#count loops
  	
  	if k==1:
  		Lk=bk-ak
  	else:
  		Lk=Lk*(float(fibonacci2(N-k+1))/float(fibonacci2(N-k+2)))
  	
  	Ik=Lk*(float(fibonacci2(N-k-1))/float(fibonacci2(N-k+1)))
  	
  	if k==1:						#first interval, lense always moves forward
  		x1k=int(round(ak+Ik))
  		focus.go_to_position(x1k)
  		img=cam.GrabOne(1000).Array[aoi[1]:aoi[3],aoi[0]:aoi[2]]
  		y1k=fm.fm(img,'TENENGRAD1',5,0).mean()
  		x2k=int(round(bk-Ik))
  		focus.go_to_position(x2k)
  		img=cam.GrabOne(1000).Array[aoi[1]:aoi[3],aoi[0]:aoi[2]]
  		y2k=fm.fm(img,'TENENGRAD1',5,0).mean()
  		goto=x2k
  		
  	elif which==1:
  		x1k=int(round(ak+Ik))		#calculate next position
  		
  		if x1k>goto:				#determine moving direction, depending on direction, determine offset
  			dir=1
  			offset=hysteresis		
  		else:
  			dir=0
  			offset=-1*hysteresis
  		goto=x1k					#save theoretical position
  		
  		pos=x1k+offset				#actual position = theoretical position + offset
  		focus.go_to_position(pos)	#move lense
  		img=cam.GrabOne(1000).Array[aoi[1]:aoi[3],aoi[0]:aoi[2]]	#grab image
  		y1k=fm.fm(img,'TENENGRAD1',5,0).mean()	#calculate contrast
  	elif which==2:
  		x2k=int(round(bk-Ik))		#calculate next position
  		
  		if x2k>goto:				#determine moving direction, depending on direction, determine offset
  			dir=1
  			offset=hysteresis
  		else:
  			dir=0
  			offset=-1*hysteresis
  		goto=x2k					#save theoretical position
  		
  		pos=x2k+offset				#actual position = theoretical position + offset
  		focus.go_to_position(pos)	#move lense
  		img=cam.GrabOne(1000).Array[aoi[1]:aoi[3],aoi[0]:aoi[2]]	#grab image
  		y2k=fm.fm(img,'TENENGRAD1',5,0).mean()	#calculate contrast
  		
  	if abs(x1k-x2k)<tolerance:		#if interval is smaller than tolerance: break
  		break
  				
  	if y1k>y2k:
  		bk=x2k
  		x2k=x1k
  		y2k=y1k
  		which=1
  	else:
  		ak=x1k
  		x1k=x2k
  		y1k=y2k
  		which=2  
  #depending on last step direction and maximum value, the return value must include offset to compensate hysteresis		
  if (dir==0) and (which==1):
  	return x1k,y1k,nCount
  elif (dir==1) and (which==2):
  	return x2k,y2k,nCount
  elif (dir==1) and (which==1):
  	return x2k-hysteresis,y2k,nCount
  elif (dir==0) and (which==2):
  	return x2k+hysteresis,y2k,nCount
    
def fibonacci(val):
#calculates value k and index n of biggest element of fibonacci series for which k<val is true
    if val<=0:
        return 1,0
    elif val==1:
        return 2,2
    else:
        kmin1=1
        kmin2=1
        k=2
        n=2
        while k<val:
            n+=1
            kmin2=kmin1
            kmin1=k
            k=kmin1+kmin2 
        return k,n
    
def fibonacci2(nin):
#calculates value k for biggest element of fibonacci series for which k<val is true
    if nin<=0:
        return 1
    elif nin==1:
        return 1
    else:
        kmin1=1
        kmin2=1
        k=2
        n=2
        while n<nin:
            n+=1
            kmin2=kmin1
            kmin1=k
            k=kmin1+kmin2 
        return k
		
def global_peak_single_step_debug(cam,focus,step,start,stop,aoi):
  # steps through complete fm curve using coarse steps
  # returns timer value for global fm maximum, fm maximum value and number of steps
  max_fm=0		#maximum fm value
  max_index=0		#timer value corresponding to maximum fm value
  index=start		#first timer value
  fm_vals=[]
  fm = ContrastMeasures()
  #loop through timer values
  while index<=stop:
  	focus.go_to_position(index) #move lense to next position
  	img=cam.GrabOne(1000).Array[aoi[1]:aoi[3],aoi[0]:aoi[2]]	
  	#grab image and calculate fm value in AOI
  	fm_vals.append(fm.fm(img,'TENENGRAD1',7,0).mean())
  	index+=step #calculate next timer value    
  return fm_vals
	
def global_peak_single_step(cam,focus,step,start,stop,aoi):
  # steps through complete fm curve using coarse steps
  # returns timer value for global fm maximum, fm maximum value and number of steps
  max_fm=0		#maximum fm value
  max_index=0		#timer value corresponding to maximum fm value
  index=start		#first timer value
  steps=0			#number of steps
  fm = ContrastMeasures()
  #loop through timer values
  while index<=stop:
  	focus.go_to_position(index) #move lense to next position
  	img=cam.GrabOne(1000).Array[aoi[1]:aoi[3],aoi[0]:aoi[2]]	
  	#grab image and calculate fm value in AOI
  	fm_val=fm.fm(img,'TENENGRAD1',7,0).mean()
  	if fm_val > max_fm:	#check if maximum occured
  		max_fm=fm_val	#save maximum fm value
  		max_index=index	#save timer value corresponding to maximum fm value
  	steps+=1	#increase number of steps
  	index+=step #calculate next timer value    
  return max_index,max_fm,steps	
	
def global_peak_two_step(cam,focus,c_step,f_step,start,stop,aoi,hysteresis):
# steps through complete fm curve using coarse steps
# applies fine step search around maximum
# returns timer value for global fm maximum, fm maximum value and number of steps
	#apply coarse step peak search
	cmax,cfm,csteps=global_peak_single_step(cam,focus,c_step,start,stop,aoi) 
	#calculate new start and stop values for fine step search
	if cmax<c_step:
		s0=0
	else:
		s0=cmax-c_step
	#apply fine step peak search	
	print(s0,cmax+c_step)
	fmax,ffm,fsteps=global_peak_single_step(cam,focus,f_step,s0-hysteresis,cmax+c_step-hysteresis,aoi)
	#total number of steps = number of steps for coarse search + number of steps for fine search
	steps=csteps+fsteps	
	return fmax,ffm,steps
	
	
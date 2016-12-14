
# coding: utf-8

# In[1]:

#import af_control as afc
import LenseController as LenseController


# In[2]:

#You need to find 
lc = LenseController.LenseController()


# In[ ]:

lc.open()


# In[4]:

lc.iris.enable()


# In[10]:

lc.iris.get_position()


# In[6]:

lc.iris.go_to_position(100)


# In[7]:

lc.iris.go_to_max()


# In[9]:

lc.iris.go_to_min()


# In[ ]:




# In[ ]:




# In[11]:

lc.zoom.enable()


# In[14]:

lc.zoom.get_position()


# In[15]:

lc.zoom.go_to_min()


# In[13]:

lc.zoom.go_to_max()


# In[ ]:




# In[ ]:




# In[7]:

lc.focus.enable()


# In[8]:

lc.focus.get_position()


# In[10]:

lc.focus.go_to_min()


# In[9]:

lc.focus.go_to_max()


# In[10]:

lc.focus.disable()


# In[77]:

lc.focus.go_to_position(900)


# In[ ]:

lc.close()


# In[ ]:




#!/usr/bin/python
import sys
import os
from Maltego import *

sys.stderr = sys.stdout

def main():

    print "Content-type: xml\n\n";
    MaltegoXML_in = sys.stdin.read()
    if MaltegoXML_in <> '':
        m = MaltegoMsg(MaltegoXML_in)
    
        # Shows inputs in client as error message
        # Enable debug on this transform in TDS to see 
        # Comment this section to run the transform
#        print 'Type='+ m.Type +'  Value='+ m.Value + '  Weight=' + m.Weight + '  Limit=' + m.Slider
#        print '\nAdditional fields:'
#        for item in m.AdditionalFields.keys():
#            print 'N:'+item+'  V:'+m.AdditionalFields[item]
        
#        print "\nTransform settings:"
#        for item in m.TransformSettings.keys():
#            print "N:"+item+" V:"+m.TransformSettings[item]
        
#        print "\n\nXML received: \n" + MaltegoXML_in
        # Comment up to here..     
    
    
    
    
        # Start writing your transform here!                
        # This one works on Person Entity as input
        # Swaps firstname and lastname, weight of 99, adds age field
        # Needs'Age' and 'ImageURL' transform settings
        
#        Age="0"
#        if m.TransformSettings["Age"] is not None:
#            Age = m.TransformSettings["Age"]

        TRX = MaltegoTransform()
    
        Ent=TRX.addEntity("maltego.Person","doesnotmatter_its_computed")
        Ent.setWeight(99)
        Ent.addAdditionalFields("firstname","First Names","strict",m.AdditionalFields["lastname"])
        Ent.addAdditionalFields("lastname","Surname","strict",m.AdditionalFields["firstname"])
        #Ent.addAdditionalFields("Age","Age of Person","strict",Age)
        
#        if m.TransformSettings["ImageURL"] is not None:
 #           Ent.setIconURL(m.TransformSettings["ImageURL"])
        
        TRX.returnOutput()
    

##
main()
                

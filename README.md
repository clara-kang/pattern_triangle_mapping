# Affine Triangle Pattern Mapping
The extension maps a pattern from a boundary triangle to others using affine mapping.

#### Step 1
The extension is at Extensions -> Generate from Path -> Triangle Pattern
<img src="https://github.com/clara-kang/pattern_triangle_mapping/blob/master/screenshots/step1.png"/>

When the window pops up just click on "apply"
<img src="https://github.com/clara-kang/pattern_triangle_mapping/blob/master/screenshots/step2.PNG"/>
<br/>

Applying for the first time will creates a layer called "Triangle Boundary"<br/>
Draw a triangle in this layer with Bezier(pen) tool<br/>
Make sure that there is exactly one element, that is the boundary triangle, in the Triangle Boundary layer
<img src="https://github.com/clara-kang/pattern_triangle_mapping/blob/master/screenshots/step3.PNG"/>
<br/>

#### Step 2
Create a pattern, when it's done, convert it to path<br/>
The position of the pattern relative to the boundary triangle will be its position in the triangles that the extension apply it to
<img src="https://github.com/clara-kang/pattern_triangle_mapping/blob/master/screenshots/step4.PNG"/>
<br/>

Now convert the objects into pattern
<img src="https://github.com/clara-kang/pattern_triangle_mapping/blob/master/screenshots/step5.PNG"/>
<br/>

The ids of the pattern can be found using the xml editor under Edit -> XML Editor<br/>
The patterns are under "defs"
<img src="https://github.com/clara-kang/pattern_triangle_mapping/blob/master/screenshots/step6.PNG"/>
<br/>

#### Step 3
Create some new triangles with Bezier(pen) tool<br/>
Select the triangles, and apply the extension again
<img src="https://github.com/clara-kang/pattern_triangle_mapping/blob/master/screenshots/step7.PNG"/>
<br/>

This time enter the id of the pattern you wish to apply<br/>
If "default" is used, the first pattern in the list will be used
<img src="https://github.com/clara-kang/pattern_triangle_mapping/blob/master/screenshots/step8.PNG"/>
<br/>

And the patterns are mapped to the triangles
<img src="https://github.com/clara-kang/pattern_triangle_mapping/blob/master/screenshots/step9.PNG"/>

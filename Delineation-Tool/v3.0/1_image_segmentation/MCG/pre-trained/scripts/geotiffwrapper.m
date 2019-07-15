function [] = geotiffwrapper(I,C,res,filename)
%----------------------GEOTIFF WRAPPER FUNCTION---------------
%Initial version
%
%
%Date   : 28-10-2015
%
%- Function to create metadata-file for geotiffwrite-function by Jimmy Shen
%- Only works for orthographic images with regular extent around camera
%  recording location
%- Hardcoded RD New projection
%- Saves file in root
%- Input: I - image
%-        C - world coordinates of image centre
%-        res - image resolution
%         filename - guess what? 
S = size(I);
%Build metadata
A.GTModelTypeGeoKey = 1;
A.GTRasterTypeGeoKey = 2;
A.ModelPixelScaleTag = [res;res;0];
% A.ModelTiepointTag = [S(1)/2;S(2)/2;0;C(1,1);C(2,1);0];
A.ModelTiepointTag = [0;0;0;C(1,1);C(2,1);0];
A.ProjectedCSTypeGeoKey = 32737;
A.ProjLinearUnitsGeoKey = 9001;
A.VerticalUnitsGeoKey = 9001;
%Pass metadata and image file to geotiffwrite-function
geotiffwrite([filename], [], I,16, A);

% Set EPSG Code in lib > geotiffwrapper.m to that if input image:
% A.ProjectedCSTypeGeoKey = 32735; (Rwanda)
% A.ProjectedCSTypeGeoKey = 32737; (Kenya)
% A.ProjectedCSTypeGeoKey = 20137; (Ethiopia)







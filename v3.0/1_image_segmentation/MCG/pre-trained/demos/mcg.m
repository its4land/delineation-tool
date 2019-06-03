
%% BMP project: Demo to show the results of the Ultrametric Contour Map obtained by SCG

% Author: 		M. Yang, 2017 with modifications from S.Crommelinck, 2018
% Description: 	This script applies SCG (improved version of gPb-ucm) on UAV images.  
% For use on a Linux computer only
% This code is largely based on the MCG package presented in:
%    Arbelaez P, Pont-Tuset J, Barron J, Marques F, Malik J,
%    "Multiscale Combinatorial Grouping,"
%    Computer Vision and Pattern Recognition (CVPR) 2014.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Clean-up %%
clear all; close all; clc;

%% Predefinfe variables %%
% Parameter for UCM threshold, the lower the more boundaries
ks = 0.1;
ext = '_mcg01';

% Data directory of input tiled imagery (RGB) and corresponding .tfw files
myDir = '/xxx/MCG/pre-trained/demos/data';                            

% Data directory of output boundary map
outputDir = '/xxx/MCG/pre-trained/demos/data';

%% Apply SCG-ucm on UAV images (one tile)
% Get all .tif files in data directory
myFiles = dir(fullfile(myDir,'*.tif'));

% Loop over all files
for k = 1:length(myFiles)  
    
    % Input .tif files
    [~,name,~] = fileparts(myFiles(k).name);
    imgFile = fullfile(myDir,[name '.tif']);
    
    % Input .tfw files
    tfwFile = fullfile(myDir,[name '.tfw']);
    if exist(tfwFile) == 2      
	
    % Open TFW File and read its content
       fileID = fopen(tfwFile);
       K = textscan(fileID, '%s','delimiter', '\n');
       
       % Store resolution in new variable
       res = str2double(K{1}{1});
       
       % Store coordinates of upper left corner in new variable
       x_corner = str2double(K{1}{5});
       y_corner = str2double(K{1}{6});
       corner = [x_corner;y_corner];
       
       % Close .tfw File
       fclose(fileID);
    end
   
    % Output files    
    outFile_mcg = fullfile(outputDir,[strcat(name,ext) '.tif']);
    
    % Read input image
    I = imread(imgFile);

    % Test the 'fast' version of SCG-Ultrametric Contour Map
    tic;
    ucm2_scg = im2ucm(I,'fast');
    toc;
    
    % Create ucm map
    ucm = ucm2_scg(3:2:end, 3:2:end);
    
    % Create bdry map
    bdry = (ucm >= ks);

    % Save result
    geotiffwrapper(bdry,corner,res,outFile_mcg);

end
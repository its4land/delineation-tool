% Author: 		S. Crommelinck, 2016                                                        %
% Description: 	This script applies gPb-ucm on resampled and tiled UAV orthoimages.  		%
% For use on a Linux computer only															%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Clean-up %%
clear all; close all; clc;

%% Predefine variables %%
% Add folders to search path
addpath(fullfile(pwd,'lib'));

% Data directory of input resampled and tiled UVA imagery (RGB)
myDir = '/usr/local/.../data_directory';

% Set EPSG Code in lib > geotiffwrapper.m to that if input image:

% Create file to store processing time
txtFile = fullfile(myDir,'processingTime.txt');

% Write header to .txt file
file = fopen(txtFile,'w');
fprintf(file, '%s; %s; %s\n','all/each','pixels','processingTime(seconds)');

%% Apply gPb-ucm on resampled and tiled UAV orthoimages
% Get all .tif files in data directory
myFiles = dir(fullfile(myDir,'*.tif'));

for k = 1:length(myFiles)
    %%% Define names of input and output files
    % Input files
    [~,name,~] = fileparts(myFiles(k).name);
    imgFile = fullfile(myDir,[name '.tif']);
    
    % Output files
    outFile_mat = fullfile(myDir,[name '.mat']);
    ext = '_ucm';
    outFile_ucm = fullfile(myDir,[strcat(name,ext) '.tif']);
        
    %%% Start measuring processing time
    % For each file
    tStart_each = tic;
    % For all files having the same number of pixels
    if k == 1
        tStart_all = tic;
    elseif string(myFiles(k).name(10:13)) ~= string(myFiles(k-1).name(10:13))
        tStart_all = tic;
    end
    
   %%% Handle TFW File
   % Create name of TFW File
   tfwFile = fullfile(myDir,[name '.tfw']);
   
   % Check if TFW file exists
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
       
       % Close TFW File
       fclose(fileID);
   end

    %%% Compute globalPb and hierachical regions (5Gb of RAM required)
    % Compute globalPb
    gPb_orient = globalPb(imgFile, outFile_mat);

    % Compute hierarchical regions
    %%% For boundaries
    ucm = contours2ucm(gPb_orient, 'imageSize');
    
    % Save the image first without georeference
    imwrite(ucm, outFile_ucm);
    
    % Reopen the image to save it then with georeference
    I = imread(outFile_ucm);

    % Save result
    geotiffwrapper(I,corner,res,outFile_ucm);


    %%% For regions
    ucm2 = contours2ucm(gPb_orient, 'doubleSize');

    % Convert ucm to the size of the original image
    ucm = ucm2(3:2:end, 3:2:end);
    
    % Create ucm maps for all possible segmentation scales
    for p = 1:1
        % Get the boundaries of segmentation at scale k in range [0 1]
        b = p/10;
        bdry = (ucm >= b);
        
        % Define output file
        ext = '_bdry';
        scale = int2str(p);
        outFile_bdry = fullfile(myDir,[strcat(name,ext,scale) '.tif']);
        
        % Save result
        geotiffwrapper(bdry,corner,res,outFile_bdry);
    end
    % Delete temporay file
    delete(outFile_mat);

    %%% Write processing time to external .txt file
    % For each file
    tEnd_each = toc(tStart_each);
    fprintf(file, '%s; %s; %f\n','each',myFiles(k).name(10:13),tEnd_each);
    fprintf('Processing time for single file of %s pixels: %d minutes and %.0f seconds\n',myFiles(k).name(10:13),floor(tEnd_each/60),rem(tEnd_each,60));

    % For all files having the same number fo pixels
    if k < length(myFiles)
        if string(myFiles(k).name(10:13)) ~= string(myFiles(k+1).name(10:13))
            tEnd_all = toc(tStart_all);
            fprintf(file, '%s; %s; %f\n','all',myFiles(k).name(10:13),tEnd_all);
            fprintf('Processing time for all files of %s pixels: %d minutes and %.0f seconds\n',myFiles(k).name(10:13),floor(tEnd_all/60),rem(tEnd_all,60));
        end
    end
end
%% Clean-up
fclose(file);

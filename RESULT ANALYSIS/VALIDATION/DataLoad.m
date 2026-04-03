function [Kinetic_Matrix,Time_Temp_Pairs,Measure_Ind,FDA_Rho_Time_Pair,MIdx_Denisty] = DataLoad(scale_id,exper_id,ifplot)
global KCodes
%This function utilices available data frames to generate sorted/filtered information tables, structured so that no outliers are included and times correspond.

%Description of data structures utilized:
% - Experimental_Codes.txt                              -> File containing the experimental codes utilized by each experiment of each scale.
% - Bioreactor 2020 - cinética fermentación.xlsx        -> File containing kinetic-related experimental data for laboratory scale.
% - Bin Automatizado 2020 - cinética fermentación.xlsx  -> File containing kinetic-related experimental data for plant scale.
% - Cinética Industrial 2020.xlsx                       -> File containing kinetic-related experimental data for industrial scale.
% - FDA_DATA.txt                                        -> File containing FDA adittion-related experimental data for all scales.
% - strcat(code,'.xlsx')                                -> Varies with code definition. Calls out the file containing Time-Temperature pairs.
clc
%% Experiment Name Determination

%Kinetic/Operational Code Loading
KCodes    =   readtable('Experimental_Codes.txt');
code      =   cell2mat(table2cell(KCodes(exper_id,scale_id)));

%Table Loading
if scale_id ==1
    Kinetic_Table       = readtable('Bioreactor 2020 - cinética fermentación.xlsx','Sheet',code);
    Operational_Table   = readtable(strcat(code,'.xlsx'));
elseif scale_id ==2
    Kinetic_Table       = readtable('Bin Automatizado 2020 - cinética fermentación.xlsx','Sheet',code);
    Operational_Table   = readtable(strcat(code,'.xlsx'));
elseif scale_id ==4
    Kinetic_Table       = readtable('Cinética Industrial 2020.xlsx','Sheet',code);
    Operational_Table   = readtable(strcat(code,'.xlsx'));
end

%Display Message
clc
fprintf('\n Loading of Database %s succesfull. \n',code)

%% Data Pre-process

%Experimental time obtention (In hours)

if scale_id == 1
    k_time  =   Kinetic_Table.Time_min_./60;
    o_time  =   Operational_Table.TIME./60;
else
    k_time  =    Kinetic_Table.Time_min_./60;
    if iscell(Operational_Table.IndiceDeTiempo(:)), o_time  = str2num(char((Operational_Table.IndiceDeTiempo(:)))).*24; else, o_time  = Operational_Table.IndiceDeTiempo(:).*24; end
end

%Reduction of operational time to the period considered by the kinetic time
    
%Date reduction - we define the dates (yyyy-mm-dd) which the experimental data for kinetic analysis was measured. 
%Then, we filter operational data to obtain points included by the sampling period.

upper_t_lim     = datetime(Kinetic_Table.Fecha(end),'InputFormat','yyyy-MM-dd HH:mm:ss');         %Date of last measurement
lower_t_lim     = datetime(Kinetic_Table.Fecha(1),'InputFormat','yyyy-MM-dd HH:mm:ss');           %Date of first measurement

if scale_id    ~= 1
    date_ind    = find(isbetween(datetime(Operational_Table.Fecha),lower_t_lim,upper_t_lim));     %Data indexes for considered period
    dates       = datetime(Operational_Table.Fecha,'Format','yyyy-MM-dd HH:mm:SS');
else
    hours       = datetime(Operational_Table.HORA,'ConvertFrom','excel', 'Format','HH:mm:ss');
    dates       = datetime(Operational_Table.FECHA,'Format','MM/dd/yyyy HH:mm:SS') + timeofday(hours);
    date_ind    = find(isbetween(dates,lower_t_lim,upper_t_lim));
end

%Temperature obtention - we use the previously obtained time indexes to identify the must temperatures we must consider for the sampling time


if scale_id    ~= 1
    temp_ind    = [];                                                                                %Vector containing indexes of non empty Must Temperatures
    for i       = 1:length(Operational_Table.EjeMosto), if ~isempty(char(Operational_Table.EjeMosto(i))), temp_ind = [temp_ind; i];  end, end 
    o_time          = o_time(intersect(date_ind,temp_ind));                                         %Operational time filtered 
    o_time          = o_time - o_time(1);                                                           %Redefinition of time based on first point
    %Operational temperatures filtered
    if iscell(Operational_Table.EjeMosto), o_temp  = str2num(char(Operational_Table.EjeMosto(intersect(date_ind,temp_ind)))); else, o_temp  = Operational_Table.EjeMosto(intersect(date_ind,temp_ind)); end
else
    temp_ind    = [];
    for i       = 1:length(Operational_Table.T_MOSTO), if ~isempty(Operational_Table.T_MOSTO(i)),         temp_ind = [temp_ind; i];  end, end 
    o_time          = o_time(intersect(date_ind,temp_ind));                                         %Operational time filtered 
    o_time          = o_time - o_time(1);                                                           %Redefinition of time based on first point
    o_temp          = Operational_Table.T_MOSTO(intersect(date_ind,temp_ind));                      %Operational temperatures filtered
end

%% Kinetic-Operational Cross-points/ Thinnig

%This section is designed to obtain the indexes of the operation points corresponding to the kinetic points
%and to reduce the number of data points while keeping it representative.

k_o_ind = ones(length(k_time)-1,1);                     %Cross index list
for i   = 2:length(k_time)                              %Crossing Loop
        [~,ind]     = min(abs(o_time-k_time(i)));
        k_o_ind(i)  = ind;
end

%The thining will be done by taking one out of 100 points

o_time_th  = o_time(1:100:length(o_time)); if scale_id == 2 && exper_id == 7, o_time_th = o_time(1:5:length(o_time)); end
o_temp_th  = o_temp(1:100:length(o_temp)); if scale_id == 2 && exper_id == 7, o_temp_th = o_temp(1:5:length(o_temp)); end


%Then we add the cross-points sorted by time , reordering them as they were previosly ordered.
orig_length   = length(o_time_th);                          %Number of original time-temp points (without cross-points)

[o_time_th,I] = sort([o_time_th(2:end);k_time]);
o_temp_th     = [o_temp_th(2:end);o_temp(k_o_ind)];
o_temp_th     = o_temp_th(I);

%Obtention of indexes of cross-points
to_find        = orig_length:1:length(o_time_th); 
Measure_Ind    = find(ismember(I,to_find));   

%Operational points matrix creation
Time_Temp_Pairs = [o_time_th o_temp_th]; %Operational points [Time(h) - Temp(C°)]


%% Kinetic_Matrix Construction

% Section designed to dilute the different concentrations included by the kinetic models
% [G F S YAN AC PF]

G   = Kinetic_Table.Glucosa_g_L_; if iscell(G), G = cell2mat(G); end
F   = Kinetic_Table.Fructosa_g_L_; if iscell(F), F = cell2mat(F); end
S   = Kinetic_Table.AzucarTotal_g_L_; if iscell(S), S = cell2mat(S); end
YAN = Kinetic_Table.YAN_mg_L_; if iscell(YAN), YAN = cell2mat(YAN); end
DD  = Kinetic_Table.Densidad_kg_m3_; if iscell(DD), DD = cell2mat(DD); end
%PF  = Kinetic_Table.Polifenoles_mg_L_; if iscell(PF), PF = cell2mat(PF); end

%Kinetic Matrix construction
Kinetic_Matrix = [G F S YAN DD];%AC PF];

%% FDA Addition point determination

FDA_Table = readtable('FDA_DATA.txt');

if      scale_id == 1
    rho_FDA     = FDA_Table.rho_FDALAB(exper_id);
    t_FDA       = o_time_th(FDA_Table.t_FDALABIdx(exper_id));
    
elseif  scale_id == 2
    rho_FDA     = FDA_Table.rho_FDACII(exper_id);
    t_FDA       = o_time_th(FDA_Table.t_FDACIIIdx(exper_id));
    
elseif  scale_id == 3
    rho_FDA     = FDA_Table.rho_FDAIND(exper_id);
    t_FDA       = o_time_th(FDA_Table.t_FDAINDIdx(exper_id));
end

%Readjustement to integrate when DAP is homogenized

if scale_id ~= 3 
    t_FDA_hom_idx       = find(ismember(o_time_th(Measure_Ind),t_FDA));
    t_FDA               = o_time_th(Measure_Ind(t_FDA_hom_idx));
else
    t_FDA_hom_idx       = find(ismember(o_time_th(Measure_Ind),t_FDA));
    t_FDA               = o_time_th(Measure_Ind(t_FDA_hom_idx));
end

%Output FDA related
FDA_Rho_Time_Pair   = [rho_FDA t_FDA];

%% Density related terms
if scale_id == 2 && exper_id ~=5
    %Load Winegrid Time-Density pairs
    Time_Density       = readtable(strcat(code,'_WineGrid','.xlsx'));
    
    %Convert to number
    if iscell((Time_Density.IndiceDeTiempo(:))) 
        D_times            = str2num(char((Time_Density.IndiceDeTiempo(:)))).*24; D_times = D_times - D_times(1);
        D_values           = str2num(char((Time_Density.DensidadSensor1(:))));
    else
        D_times            = Time_Density.IndiceDeTiempo(:).*24; D_times = D_times - D_times(1);
        D_values           = Time_Density.DensidadSensor1(:);
    end
    
    %Find measurements that are between the dates where the kinetic measurements where taken
    dates_den          = datetime(Time_Density.FechaHora,'Format','dd-MM-yyyy HH:mm:ss');
    cross_ind          = find(isbetween(Kinetic_Table.Fecha,dates_den(1),dates_den(end)));
      
    %Find time elapsed between the inoculation point and the first point from the density measurements
    t11=datevec(datenum(dates_den(1)));
    t22=datevec(datenum(lower_t_lim));
    delay = etime(t11,t22)/3600;    
    
    
    %Incorporate to the elapsed time points the delay
    delayed_times      = D_times +  delay;
    
    %Using the delayed times, obtain points corresponding to the kinetic measuremnets
    k_time  = Kinetic_Table.Time_min_./60;
    k_d_ind = ones(length(cross_ind),1);                  %Cross index list
    j = 1;
    for i   = cross_ind(1):cross_ind(end)                 %Crossing Loop
            [~,ind]     = min(abs(k_time(i)-delayed_times));
            k_d_ind(j)  = ind;
            j = j+1;
    end
    
    %Using the indexes recently obtained, get the density values
    WG_densities = medfilt1(D_values,3);
    WG_densities = WG_densities(k_d_ind);
    
    %Artificial point additon to incorporate density-time points in the same time frame that the experimental measurements
    delayed_times2 = delayed_times;
    
    for i = 1:length(k_d_ind)
       if k_time(cross_ind(i))>= delayed_times(k_d_ind(i))
           delayed_times2 = [delayed_times2(1:k_d_ind(i)); k_time(cross_ind(i)); delayed_times2(k_d_ind(i)+1:end)];
           k_d_ind(i:end) = k_d_ind(i:end) + 1;
       else
           delayed_times2 = [delayed_times2(1:k_d_ind(i)-1); k_time(cross_ind(i)); delayed_times2(k_d_ind(i):end)];
           k_d_ind(i+1:end) = k_d_ind(i+1:end) - 1;
       end
    end
    
    %Output
    MIdx_Denisty = [cross_ind WG_densities];
    
else 
    MIdx_Denisty = [NaN,NaN];
end

%% Plotting

if ifplot == true
    
    if exper_id ~= 5 && scale_id == 2
        figure()
        hold on
        plot(delayed_times,D_values,'r-')
        plot(delayed_times,medfilt1(D_values,3),'k-')
        plot(delayed_times2(k_d_ind),WG_densities,'bo','LineWidth',2)
        xlabel('Time (h)')
        ylabel('Density (kg/m^3)')
        legend('Winegrid Measurements','Filtered data','Kinetic Measurement Cross-Points')
    end
    
    figure()
    hold on
    plot(o_time,o_temp)
    plot(o_time_th,o_temp_th,'rx')
    plot(o_time(k_o_ind),o_temp(k_o_ind),'ko','LineWidth',2)
    xlabel('Time (h)')
    ylabel('Temperature °C')
    legend('Complete Data','Thinned Data','Kinetic Measurement Cross-Points')
 
end


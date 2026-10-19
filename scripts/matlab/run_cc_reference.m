% Simulate the official ARCH-COMP Chasing Cars model on inputs exported by scripts/cc_matlab_compare.py and
% save the car positions at t = 0:10:100 s for comparison with the Python port.
%
% Requires MATLAB + Simulink (the model contains a Stateflow chart) and the model downloaded by
% scripts/fetch_cc_model.sh (external/chasing-cars/cars.mdl). Tested with MATLAB R2026b.
% Run from target_project/:
%   matlab -batch "run('scripts/matlab/run_cc_reference.m')"                     % 200 random inputs
%   matlab -batch "in_csv='falsifiers_main_inputs.csv'; out_csv='falsifiers_main_simulink.csv'; run('scripts/matlab/run_cc_reference.m')"
%   matlab -batch "input_mode='step'; reltol='1e-6'; abstol='1e-6'; out_csv='cc_outputs_simulink_step_tol1e-6.csv'; run('scripts/matlab/run_cc_reference.m')"
%   matlab -batch "input_mode='step'; reltol='1e-10'; abstol='1e-10'; minstep='auto'; out_csv='cc_outputs_simulink_step_tol1e-10.csv'; run('scripts/matlab/run_cc_reference.m')"
% Optional variables (set before run): in_csv, out_csv (file names in results/matlab/), reltol, abstol, minstep
% (strings; default: the model's own settings, e.g. MinStep 0.01 s), input_mode ('arch' (default) or 'step').
%
% input_mode 'arch' follows the ARCH run script (external/chasing-cars/run_cars.m): 'previous' interpolation on
% a 0.01 s grid, which Simulink's root inports interpolate linearly, so each switch becomes a 0.01 s ramp.
% input_mode 'step' gives exactly piecewise-constant inputs (time stamps duplicated at each switch), as in the
% Python port. Throttle = columns 1..10, brake = columns 11..20, one value per 10 s segment (our decision D3).
% Unless overridden, the model's solver settings are used unchanged (VariableStepAuto, RelTol 1e-3, AbsTol 1e-5);
% 'SpecifiedOutputTimes' makes the solver produce the outputs at exactly t = 0:10:100 instead of interpolating
% between solver steps.

if ~exist('in_csv', 'var'), in_csv = 'cc_inputs.csv'; end
if ~exist('out_csv', 'var'), out_csv = 'cc_outputs_simulink.csv'; end
if ~exist('input_mode', 'var'), input_mode = 'arch'; end
assert(any(strcmp(input_mode, {'arch', 'step'})), 'input_mode must be arch or step');
root = fullfile(fileparts(mfilename('fullpath')), '..', '..');
addpath(fullfile(root, 'external', 'chasing-cars'));
outdir = fullfile(root, 'results', 'matlab');
U = readmatrix(fullfile(outdir, in_csv));   % N x 20
load_system('cars');
opts = {};
if exist('reltol', 'var'), opts = [opts, {'RelTol', reltol}]; end
if exist('abstol', 'var'), opts = [opts, {'AbsTol', abstol}]; end
if exist('minstep', 'var'), opts = [opts, {'MinStep', minstep}]; end
T = 100;
N = size(U, 1);
ts = (0:10:100)';
Y = zeros(N, 5 * 11);
t0 = tic;
tt = sort([ts; ts(2:end-1)]);               % 'step': 0, 10, 10, 20, 20, ..., 90, 90, 100
seg = [1; reshape([1:9; 2:10], [], 1); 10];  % segment of each time stamp (old value first at a switch)
for k = 1:N
    th = U(k, 1:10); br = U(k, 11:20);
    if strcmp(input_mode, 'arch')
        uin = [[th th(end)]' [br br(end)]'];
        tq = (0:0.01:T)';
        uq = interp1(ts, uin, tq, 'previous');
        assignin('base', 'u', [tq uq]);
    else
        assignin('base', 'u', [tt th(seg)' br(seg)']);
    end
    assignin('base', 'T', T);
    out = sim('cars', 'StopTime', 'T', 'LoadExternalInput', 'on', 'ExternalInput', 'u', ...
              'SaveTime', 'on', 'TimeSaveName', 'tout', 'SaveOutput', 'on', 'OutputSaveName', 'yout', ...
              'SaveFormat', 'Array', 'OutputOption', 'SpecifiedOutputTimes', 'OutputTimes', '[0:10:100]', opts{:});
    [ok, idx] = ismembertol(ts, out.tout, 1e-9);
    assert(all(ok), 'run %d: sample times missing from tout', k);
    y = out.yout(idx, :);              % 11 samples x 5 cars
    assert(isequal(size(y), [11 5]), 'run %d: unexpected yout size', k);
    Y(k, :) = reshape(y, 1, []);       % column-major: car 1 (t = 0..100), car 2, ...
    if mod(k, 20) == 0, fprintf('%d/%d  %.1fs\n', k, N, toc(t0)); end
end
elapsed = toc(t0);
fid = fopen(fullfile(outdir, out_csv), 'w');
fprintf(fid, [repmat('%.17g,', 1, 5 * 11 - 1) '%.17g\n'], Y');
fclose(fid);
v = ver('MATLAB'); vs = ver('Simulink');
[~, base] = fileparts(out_csv);
fid = fopen(fullfile(outdir, [base '_meta.txt']), 'w');
fprintf(fid, 'MATLAB %s %s; Simulink %s %s\n', v.Version, v.Release, vs.Version, vs.Release);
fprintf(fid, 'inputs: results/matlab/%s (input_mode %s); model: external/chasing-cars/cars.mdl\n', in_csv, input_mode);
fprintf(fid, 'model solver %s, RelTol %s, AbsTol %s, MaxStep %s, MinStep %s; overrides: %s\n', ...
        get_param('cars', 'SolverName'), get_param('cars', 'RelTol'), get_param('cars', 'AbsTol'), ...
        get_param('cars', 'MaxStep'), get_param('cars', 'MinStep'), ...
        strjoin(cellfun(@char, opts, 'UniformOutput', false), ' '));
fprintf(fid, '%d simulations, %.1f s total (%.3f s each), finished %s\n', N, elapsed, elapsed / N, ...
        char(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss')));
fclose(fid);
close_system('cars', 0);
fprintf('wrote results/matlab/%s (%d runs, %.1f s)\n', out_csv, N, elapsed);

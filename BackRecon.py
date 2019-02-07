import os
from nipype.interfaces.base import File, traits
from nipype.interfaces.matlab import MatlabCommand, MatlabInputSpec

ALGORITHM_FILES = dict(
    gigica="icatb_gigicar",
    dualregress="icatb_dualregress"
)
DEFAULT_ALGORITHM = "gigica"
DEFAULT_MASK = "mask.nii"
DEFAULT_ICA_SIG = "ica_sig.mat"


class BackReconInputSpec(MatlabInputSpec):
    algorithm = traits.Str(mandatory=False,
                           default_value=DEFAULT_ALGORITHM,
                           desc='Algorithm to use for Back-Reconstruction')
    mask = traits.Str(mandatory=False,
                      default_value=DEFAULT_MASK,
                      desc='Mask to use for Back-Reconstruction')
    ica_sig = traits.Str(mandatory=True,
                         desc=".Mat file containing ICA Signals")
    files = traits.List(mandatory=True,
                        desc='List of Files for Back-Reconstruction')


class BackReconOutputSpec(MatlabInputSpec):
    matlab_output = traits.Str()


class BackRecon(MatlabCommand):
    """ Basic Hello World that displays Hello <name> in MATLAB

    Returns
    -------

    matlab_output : capture of matlab output which may be
                    parsed by user to get computation results

    Example
    --------

    >>> recon = BackRecon()
    >>> recon.inputs.files = ['subject_1.nii', 'subject_2.nii']
    >>> recon.inputs.mask = 'mask.nii'
    >>> recon.inputs.ica_sig = 'gica_signal.mat'
    >>> recon.inputs.algorithm = 'gigica'
    >>> out = recon.run()
    """
    input_spec = BackReconInputSpec
    output_spec = BackReconOutputSpec

    def _runner_script(self):
        files_line = {"%s" % file for file in self.inputs.files}
        script = """
            addpath('matcode');
            ica_sig = load('%s');
            ica_sig = ica_sig.SM;
            files = %s;
            mask = load('%s');
            mask_data = mask.mask;
            for i = 1:length(files)
                nii = load_nii(files{i});
                data = reshape(nii.img, [prod(size(nii.img)(1:3)), size(nii.img, 4)]);
                masked_data = data(mask==1, :);
                data = icatb_preproc_data(masked_data);
                [TC, SM] = %s(data, ica_sig);
                save([files{i} '.backrecon.mat'],'TC','SM')
            end
        """ % (self.inputs.ica_sig,
               files_line,
               self.inputs.mask,
               ALGORITHM_FILES.get(self.inputs.algorithm, DEFAULT_ALGORITHM)
               )
        print("MATLAB SCRIPT IS %s" % script)
        return script

    def run(self, **inputs):
        # inject your script
        self.inputs.script = self._runner_script()
        results = super().run(**inputs)
        stdout = results.runtime.stdout
        # attach stdout to outputs to access matlab results
        results.outputs.matlab_output = stdout
        return results

    def _list_outputs(self):
        outputs = self._outputs().get()
        return outputs


if __name__ == "__main__":
    recon = BackRecon()
    recon.inputs.files = ['subject_1.nii', 'subject_2.nii']
    recon.inputs.mask = 'mask.mat'
    recon.inputs.ica_sig = 'gica_signal.mat'
    recon.inputs.algorithm = 'gigica'
    out = recon.run()

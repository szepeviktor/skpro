
class DPQRMixin():
    """Mixin class for all the distribution class
    
    Notes
    -----
    Used by 'DistributionBase' class. 
    'DistributionBase' inherits thus a serie of 'DQPR' abstract method 
    to be then instanciated in the concrete distribution sub-classes
    
    """
    
    def pdf_imp(self, X):
        """Return the vectorized pdf of the concrete distribution
         
         Parameters
         ----------
         X : array-like, shape = (n_samples, n_features)
            Test samples

         Returns
         -------
         pdf output : array of float

         """
        raise ValueError('pdf function not implemented')
        
        
    def pmf_imp(self, X):
        """Return the vectorized pmf of the concrete distribution
         
         Parameters
         ----------
         X : array-like, shape = (n_samples, n_features)
            Test samples

         Returns
         -------
         pmf output : array of float

         """
        raise ValueError('pmf function not implemented')

    def cdf_imp(self, X):
        """Return the vectorized cdf of the concrete distribution
         
         Parameters
         ----------
         X : array-like, shape = (n_samples, n_features)
            Test samples

         Returns
         -------
         cdf output : array of float

         """
        raise ValueError('cdf function not implemented')
    
    
    def squared_norm_imp(self):
        """Return the vectorized pdf of the concrete distribution

         Returns
         -------
         pdf output : array of float

         """
        raise ValueError('squared_norm function not implemented')
        
        

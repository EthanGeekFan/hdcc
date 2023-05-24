from __future__ import annotations
from enum import Enum
import numpy as np

class Representation(Enum):
    BSC = "BSC"
    MAP_B = "MAP-B"
    MAP_I = "MAP-I"
    MAP_C = "MAP-C"
    HRR = "HRR"
    FHRR = "FHRR"
    VTB = "VTB"
    MBAT = "MBAT"
    BSDC_CDT = "BSDC-CDT"
    BSDC_S = "BSDC-S"
    BSDC_SEG = "BSDC-SEG"


class HyperVector:
    data: np.array
    dim: int
    repr: Representation

    def __str__(self) -> str:
        return f"{self.repr}({self.dim}) {self.data}"


class HV_FHRR(HyperVector):
    def __init__(self, dim: int, data = None):
        self.dim = dim
        self.repr = Representation.FHRR
        # generate iid data from uniform distribution [-pi, pi)
        if data is not None:
            self.data = np.array(data)
        else:
            self.data = np.random.uniform(-np.pi, np.pi, self.dim)
        pass

    def sim(self, other: HV_FHRR) -> float:
        # average of cosines of angles between two vectors
        assert self.dim == other.dim
        return np.mean(np.cos(self.data - other.data))

    def bind(self, other: HV_FHRR) -> HV_FHRR:
        # bind two vectors
        assert self.dim == other.dim
        data = self.data + other.data
        res = HV_FHRR(self.dim, data)
        HV_FHRR.wrap_vector(res)
        HV_FHRR.check_range([res])
        return res
    
    def unbind(self, other: HV_FHRR) -> HV_FHRR:
        # unbind two vectors
        # TODO: check if this is correct
        assert self.dim == other.dim
        data = other.data - self.data
        res = HV_FHRR(self.dim, data)
        HV_FHRR.wrap_vector(res)
        HV_FHRR.check_range([res])
        return res
    
    @staticmethod
    def check_range(vectors: list[HV_FHRR]):
        # assert all data in v is between -pi and pi
        if not all([np.all(v.data >= -np.pi) and np.all(v.data <= np.pi) for v in vectors]):
            for v in vectors:
                print(v)
            raise Exception("Data in vectors must be between -pi and pi")
    
    @staticmethod
    def bundle(vectors: list[HV_FHRR]) -> HV_FHRR:
        # bundle multiple vectors
        # angles of element addition
        # convert the angles to unit complex exponential then add then convert back to angles
        dim = vectors[0].dim
        HV_FHRR.check_range(vectors)
        assert all([v.dim == dim for v in vectors])
        # data = np.angle(np.sum(np.exp(1j * np.array([v.data for v in vectors])), axis=0))
        vectors = np.array([v.data for v in vectors])
        data = np.arctan2(np.sum(np.sin(vectors), axis=0), np.sum(np.cos(vectors), axis=0))
        res =  HV_FHRR(dim, data)
        HV_FHRR.wrap_vector(res)
        return res
    
    @staticmethod
    def wrap_vector(v: HV_FHRR):
        # wrap vector to [-pi, pi)
        while np.any(v.data > np.pi) or np.any(v.data < -np.pi):
            v.data = np.where(v.data > np.pi, v.data - 2 * np.pi, v.data)
            v.data = np.where(v.data < -np.pi, v.data + 2 * np.pi, v.data)
    
    def frac_bind(self, frac: float) -> HV_FHRR:
        # bind vector with real number
        data = frac * self.data
        res = HV_FHRR(self.dim, data)
        HV_FHRR.wrap_vector(res)
        HV_FHRR.check_range([res])
        return res


class HV_HRR(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.HRR
        # generate iid data from normal distribution with mean 0 and variance 1 / dim
        self.data = np.random.normal(0, 1 / dim, self.dim)
        pass

    def sim(self, other: HV_HRR):
        # cosine similarity: cosine of angle between two vectors
        assert self.dim == other.dim
        data = np.dot(self.data, other.data) / np.linalg.norm(self.data) / np.linalg.norm(other.data)
        return data
    
    def bind(self, other: HV_HRR) -> HV_HRR:
        # circular convolution
        # TODO: check if this is correct
        assert self.dim == other.dim
        data = np.fft.ifft(np.fft.fft(self.data) * np.fft.fft(other.data)).real
        return HV_HRR(self.dim, data)
    
    def unbind(self, other: HV_HRR) -> HV_HRR:
        # circular correlation
        # TODO: check if this is correct
        assert self.dim == other.dim
        data = np.fft.ifft(np.fft.fft(self.data) * np.conj(np.fft.fft(other.data))).real
        return HV_HRR(self.dim, data)
    
    def bundle(self, other: HV_HRR) -> HV_HRR:
        # bundle two vectors
        # element-wise addition with normalization
        assert self.dim == other.dim
        data = (self.data + other.data) / np.linalg.norm(self.data + other.data)
        return HV_HRR(self.dim, data)
    
    def frac_bind(self, frac: float) -> HV_HRR:
        # bind vector with real number
        # TODO: check if this is correct
        raise NotImplementedError
        res = np.fft.ifft(np.fft.fft(self.data)**frac).real
        res /= np.linalg.norm(res)
        return HV_HRR(self.dim, res)


class HV_MAP_C(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.MAP_C
        # generate iid data from uniform distribution [-1, 1)
        self.data = np.random.uniform(-1, 1, self.dim)
        pass

    def sim(self, other: HV_MAP_C) -> float:
        # cosine similarity: cosine of angle between two vectors
        assert self.dim == other.dim
        return np.dot(self.data, other.data) / np.linalg.norm(self.data) / np.linalg.norm(other.data)
    
    def bind(self, other: HV_MAP_C) -> HV_MAP_C:
        # element-wise multiplication
        assert self.dim == other.dim
        data = self.data * other.data
        return HV_MAP_C(self.dim, data)
    
    def unbind(self, other: HV_MAP_C) -> HV_MAP_C:
        # element-wise multiplication
        assert self.dim == other.dim
        data = self.data * other.data
        return HV_MAP_C(self.dim, data)
    
    def bundle(self, other: HV_MAP_C) -> HV_MAP_C:
        # element-wise addition with cutting
        assert self.dim == other.dim
        data = np.clip(self.data + other.data, -1, 1)
        return HV_MAP_C(self.dim, data)
    
    def frac_bind(self, frac: float) -> HV_MAP_C:
        # bind vector with real number
        # TODO: implement
        raise NotImplementedError


class HV_MAP_I(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.MAP_I
        # generate iid data from binomial distribution with probability 0.5
        self.data = np.random.binomial(1, 0.5, self.dim) * 2 - 1
        pass

    def sim(self, other: HV_MAP_I) -> float:
        # cosine similarity: cosine of angle between two vectors
        assert self.dim == other.dim
        return np.dot(self.data, other.data) / np.linalg.norm(self.data) / np.linalg.norm(other.data)
    
    def bind(self, other: HV_MAP_I) -> HV_MAP_I:
        # element-wise multiplication
        assert self.dim == other.dim
        data = self.data * other.data
        return HV_MAP_I(self.dim, data)
    
    def unbind(self, other: HV_MAP_I) -> HV_MAP_I:
        # element-wise multiplication
        assert self.dim == other.dim
        data = self.data * other.data
        return HV_MAP_I(self.dim, data)
    
    def bundle(self, other: HV_MAP_I) -> HV_MAP_I:
        # element-wise addition
        assert self.dim == other.dim
        data = self.data + other.data
        return HV_MAP_I(self.dim, data)
    
    def frac_bind(self, frac: float) -> HV_MAP_I:
        # bind vector with real number
        # TODO: implement this
        raise NotImplementedError


class HV_MAP_B(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.MAP_B
        # generate iid data from binomial distribution with probability 0.5
        self.data = np.random.binomial(1, 0.5, self.dim) * 2 - 1
        pass

    def sim(self, other: HV_MAP_B) -> float:
        # cosine similarity: cosine of angle between two vectors
        assert self.dim == other.dim
        return np.dot(self.data, other.data) / np.linalg.norm(self.data) / np.linalg.norm(other.data)
    
    def bind(self, other: HV_MAP_B) -> HV_MAP_B:
        # element-wise multiplication
        assert self.dim == other.dim
        data = self.data * other.data
        return HV_MAP_B(self.dim, data)
    
    def unbind(self, other: HV_MAP_B) -> HV_MAP_B:
        # element-wise multiplication
        assert self.dim == other.dim
        data = self.data * other.data
        return HV_MAP_B(self.dim, data)
    
    def bundle(self, other: HV_MAP_B) -> HV_MAP_B:
        # element-wise addition with threshold
        # TODO: check if this is correct
        assert self.dim == other.dim
        data = np.where(self.data + other.data > 0, 1, -1)
        return HV_MAP_B(self.dim, data)
    
    def frac_bind(self, frac: float) -> HV_MAP_B:
        # bind vector with real number
        raise NotImplementedError


class HV_BSC(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.BSC
        # generate iid data from binomial distribution with probability 0.5
        self.data = np.random.binomial(1, 0.5, self.dim)
        pass

    def sim(self, other: HV_BSC) -> float:
        # 1 - hamming distance/dim: fraction of identical bits
        assert self.dim == other.dim
        return np.mean(self.data == other.data)
    
    def bind(self, other: HV_BSC) -> HV_BSC:
        # element-wise XOR since data is either 0 or 1
        assert self.dim == other.dim
        data = np.logical_xor(self.data, other.data)
        return HV_BSC(self.dim, data)
    
    def unbind(self, other: HV_BSC) -> HV_BSC:
        # element-wise XOR since data is either 0 or 1
        assert self.dim == other.dim
        data = np.logical_xor(self.data, other.data)
        return HV_BSC(self.dim, data)
    
    def bundle(self, other: HV_BSC) -> HV_BSC:
        # element-wise addition with threshold
        # TODO: check for multiple bundles
        assert self.dim == other.dim
        data = np.where(self.data + other.data > 0, 1, 0)
        return HV_BSC(self.dim, data)
    
    def frac_bind(self, frac: float) -> HV_BSC:
        # bind vector with real number
        # TODO: implement
        raise NotImplementedError


class HV_VTB(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.VTB
        # generate iid data from normal distribution with mean 0 and variance 1 / dim
        self.data = np.random.normal(0, 1 / dim, self.dim)
        pass

    def sim(self, other: HV_VTB) -> float:
        # cosine similarity: cosine of angle between two vectors
        assert self.dim == other.dim
        return np.dot(self.data, other.data) / np.linalg.norm(self.data) / np.linalg.norm(other.data)
    
    def bind(self, other: HV_VTB) -> HV_VTB:
        # VTB: Vector Derived Transformation Based
        assert self.dim == other.dim
        raise NotImplementedError
    
    def unbind(self, other: HV_VTB) -> HV_VTB:
        # VTB: Vector Derived Transformation Based
        assert self.dim == other.dim
        raise NotImplementedError
    
    def bundle(self, other: HV_VTB) -> HV_VTB:
        # VTB: Vector Derived Transformation Based
        assert self.dim == other.dim
        raise NotImplementedError
    
    def frac_bind(self, frac: float) -> HV_VTB:
        # bind vector with real number
        raise NotImplementedError



class HV_MBAT(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.MBAT
        # generate iid data from normal distribution with mean 0 and variance 1 / dim
        self.data = np.random.normal(0, 1 / dim, self.dim)
        pass

    def sim(self, other: HV_MBAT) -> float:
        # cosine similarity: cosine of angle between two vectors
        assert self.dim == other.dim
        return np.dot(self.data, other.data) / np.linalg.norm(self.data) / np.linalg.norm(other.data)
    
    def bind(self, other: HV_MBAT) -> HV_MBAT:
        # MBAT: Matrix Based Transformation
        assert self.dim == other.dim
        raise NotImplementedError
    
    def unbind(self, other: HV_MBAT) -> HV_MBAT:
        # MBAT: Matrix Based Transformation
        assert self.dim == other.dim
        raise NotImplementedError
    
    def bundle(self, other: HV_MBAT) -> HV_MBAT:
        # MBAT: Matrix Based Transformation
        assert self.dim == other.dim
        raise NotImplementedError
    
    def frac_bind(self, frac: float) -> HV_MBAT:
        # bind vector with real number
        raise NotImplementedError


class HV_BSDC_CDT(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.BSDC_CDT
        # generate iid data from binomial distribution with probability p << 1. p = 1 / sqrt(dim) achieves largest capacity(recommended).
        # Rachkovskij DA, Kussul EM (2001) https://doi.org/10.1162/089976601300014592
        self.data = np.random.binomial(1, 1 / np.sqrt(dim), self.dim)
        pass

    def sim(self, other: HV_BSDC_CDT) -> float:
        # overlap similarity: fraction of identical bits
        assert self.dim == other.dim
        raise NotImplementedError
        # TODO: check if this is correct
        return np.mean(self.data == other.data == 1)
    
    def bind(self, other: HV_BSDC_CDT) -> HV_BSDC_CDT:
        # CDT
        assert self.dim == other.dim
        raise NotImplementedError
    
    def unbind(self, other: HV_BSDC_CDT) -> HV_BSDC_CDT:
        # NO UNBINDING
        assert self.dim == other.dim
        raise NotImplementedError
    
    def bundle(self, other: HV_BSDC_CDT) -> HV_BSDC_CDT:
        # Disjunction
        assert self.dim == other.dim
        raise NotImplementedError
    
    def frac_bind(self, frac: float) -> HV_BSDC_CDT:
        # bind vector with real number
        raise NotImplementedError


class HV_BSDC_S(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.BSDC_S
        # generate iid data from binomial distribution with probability p << 1. p = 1 / sqrt(dim) achieves largest capacity(recommended).
        # Rachkovskij DA, Kussul EM (2001) https://doi.org/10.1162/089976601300014592
        self.data = np.random.binomial(1, 1 / np.sqrt(dim), self.dim)
        pass

    def sim(self, other: HV_BSDC_S) -> float:
        # overlap similarity: fraction of identical bits
        assert self.dim == other.dim
        raise NotImplementedError
    
    def bind(self, other: HV_BSDC_S) -> HV_BSDC_S:
        # Shifting
        assert self.dim == other.dim
        raise NotImplementedError
    
    def unbind(self, other: HV_BSDC_S) -> HV_BSDC_S:
        # Shifting
        assert self.dim == other.dim
        raise NotImplementedError
    
    def bundle(self, other: HV_BSDC_S) -> HV_BSDC_S:
        # Disjunction (opt. thinning)
        assert self.dim == other.dim
        raise NotImplementedError
    
    def frac_bind(self, frac: float) -> HV_BSDC_S:
        # bind vector with real number
        raise NotImplementedError


class HV_BSDC_SEG(HyperVector):
    def __init__(self, dim: int):
        self.dim = dim
        self.repr = Representation.BSDC_SEG
        # generate iid data from binomial distribution with probability p << 1. p = 1 / sqrt(dim) achieves largest capacity(recommended).
        # Rachkovskij DA, Kussul EM (2001) https://doi.org/10.1162/089976601300014592
        self.data = np.random.binomial(1, 1 / np.sqrt(dim), self.dim)
        pass

    def sim(self, other: HV_BSDC_SEG) -> float:
        # overlap similarity: fraction of identical bits
        assert self.dim == other.dim
        raise NotImplementedError
    
    def bind(self, other: HV_BSDC_SEG) -> HV_BSDC_SEG:
        # Segment shifting
        assert self.dim == other.dim
        raise NotImplementedError
    
    def unbind(self, other: HV_BSDC_SEG) -> HV_BSDC_SEG:
        # Segment shifting
        assert self.dim == other.dim
        raise NotImplementedError
    
    def bundle(self, other: HV_BSDC_SEG) -> HV_BSDC_SEG:
        # Disjunction (opt. thinning)
        assert self.dim == other.dim
        raise NotImplementedError
    
    def frac_bind(self, frac: float) -> HV_BSDC_SEG:
        # bind vector with real number
        raise NotImplementedError


def fractional_binding_compatible(repr: Representation):
    # TODO: implement more types after further reasearch on fractional binding
    return repr == Representation.FHRR


def fractional_bind(base: HyperVector, value: int | float, dst: HyperVector):
    if not fractional_binding_compatible(base.repr):
        raise Exception("Fractional binding is not compatible with " + str(base.repr))
    # TODO: implement DFT for non-FHRR representations
    for i in range(base.dim):
        dst.data[i] = pow(base.data[i], value)
    pass


class HDFloat(HyperVector):
    base: HyperVector | None

    def __init__(self, dim: int = 1):
        self.dim = dim
        self.base = None
        self.repr = Representation.FHRR
        self.data = None

    def set_base(self, base: HyperVector):
        self.dim = base.dim
        self.base = base
        self.repr = base.repr
        self.data = None
    
    def assign(self, value: float):
        fractional_bind(self.base, value, self)
    
    def __str__(self):
        return "HDFloat(dim: " + str(self.dim) + ")"
    pass

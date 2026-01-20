%global optflags %{optflags} -w
%global igc_patch 10

Name: intel-igc
Version: 2.27.%{igc_patch}
Release: 1
Summary: Intel Graphics Compiler for OpenCL

License: MIT
URL: https://github.com/intel/intel-graphics-compiler
Source0: https://github.com/intel/intel-graphics-compiler/archive/v%{version}/intel-graphics-compiler-%{version}.tar.gz
Source1: https://github.com/intel/vc-intrinsics/archive/v0.24.2/vc-intrinsics-0.24.2.tar.gz

BuildRequires: cmake
BuildRequires: make
BuildRequires: git
BuildRequires: llvm-devel
BuildRequires: lld-devel
BuildRequires: clang
#BuildRequires: clang-tools-extra
BuildRequires: flex
BuildRequires: bison
BuildRequires: python3
BuildRequires: python-mako
BuildRequires: python-pyyaml
BuildRequires: pkgconfig(zlib)
BuildRequires: intel-opencl-clang-devel
BuildRequires: pkgconfig(libffi)
BuildRequires: libunwind-devel
BuildRequires: pkgconfig(libzstd)
BuildRequires: pkgconfig(LLVMSPIRVLib)
BuildRequires: spirv-llvm-translator
BuildRequires: pkgconfig(SPIRV-Headers)
BuildRequires: pkgconfig(SPIRV-Tools)

%rename intel-graphics-compiler = %{version}-%{release}

Requires:      %{name}-libs%{?_isa} = %{version}-%{release}

# from fedora
# Unfortunately, it isn't trivially posible to build with prebuilt vc-intrinsics
Provides: bundled(intel-vc-intrinsics)

%description
The Intel Graphics Compiler for OpenCL is an LLVM based compiler for OpenCL targeting Intel Gen graphics hardware architecture.

%package       devel
Summary:       Intel Graphics Compiler Frontend - Devel Files
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}

%description   devel
Devel files for Intel Graphics Compiler for OpenCL.

%package       libs
Summary:       Intel Graphics Compiler Frontend - Library Files
Requires:      %{name} = %{version}-%{release}

%description   libs
Library files for Intel Graphics Compiler for OpenCL.

%prep
tar -xf %{SOURCE1}

%autosetup -n intel-graphics-compiler-%{version} -p1

%build
%cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS:BOOL=OFF \
    -DIGC_OPTION__LLVM_PREFERRED_VERSION=21.1.8
    -DVC_INTRINSICS_SRC="%{_builddir}/vc-intrinsics-0.24.2" \
    -DIGC_API_PATCH_VERSION=%{igc_patch} \
%ifarch x86_64
    -DIGC_OPTION__ARCHITECTURE_TARGET='Linux64' \
%endif
%ifarch %{aarch64}
    -DIGC_OPTION__ARCHITECTURE_TARGET='LinuxARM' \
%endif
    -DIGC_OPTION__LINK_KHRONOS_SPIRV_TRANSLATOR=ON \
    -DIGC_BUILD__VC_ENABLED=ON \
    -DIGC_OPTION__SPIRV_TRANSLATOR_MODE=Prebuilds \
    -DIGC_OPTION__CLANG_MODE=Prebuilds \
    -DIGC_OPTION__LLD_MODE=Prebuilds \
    -DIGC_OPTION__LLVM_MODE=Prebuilds \
    -DIGC_OPTION__SPIRV_TOOLS_MODE=Prebuilds \
    -DIGC_OPTION__USE_PREINSTALLED_SPIRV_HEADERS=ON \
    -DIGC_OPTION__VC_INTRINSICS_MODE=Source \
    -DINSTALL_GENX_IR=ON \
    -Wno-dev

%make_build

%install
%make_install -C build

%files
%{_bindir}/iga{32,64}

%files libs
%license LICENSE.md
%license %{_libdir}/igc2/NOTICES.txt
%dir %{_libdir}/igc2/
%{_libdir}/libiga{32,64}.so.2.*
%{_libdir}/libigc.so.2.*+*
%{_libdir}/libigdfcl.so.2.*

%files devel
%{_libdir}/libiga{32,64}.so.2
%{_libdir}/libiga{32,64}.so
%{_libdir}/libigc.so.2
%{_libdir}/libigc.so
%{_libdir}/libigdfcl.so.2
%{_libdir}/libigdfcl.so
%{_includedir}/igc
%{_includedir}/iga
%{_includedir}/visa
%{_libdir}/pkgconfig/igc-opencl.pc

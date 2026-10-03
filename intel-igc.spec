# Intel Graphics Compiler 2.41 needs LLVM 22. OpenMandriva's system compiler
# is LLVM 23, which IGC does not support, and there is no llvm22 compat
# package. Build the compiler in source mode against a bundled LLVM 22 the
# same way Fedora's RHEL build does, and ship libopencl-clang.so.22 from here.
# The older standalone intel-opencl-clang package stays on soname .21.

%global _disable_lto 1
# -flto on a bundled LLVM blows the link and has miscompiled IGC before.
%global optflags %(echo %{optflags} | sed -e 's/ -flto//g') -w
# dwz runs out of memory on the statically linked LLVM inside libigc.
%global _find_debuginfo_dwz_opts %{nil}

%global vc_commit 27f7c4f34738f5eaf7a045b77edf8d9e034443d8
%global clang_commit b953eceebb0abc6ea954a14545420e3f97540a77
%global translator_commit 27afcfe385cf542197dfde8c658e1f5ff53fc2fc
%global spirv_headers_commit 575b6512579ebde466ed3dfc04e413439d14d95d
%global spirv_tools_commit f80351511e9c4672e284842c7b124315c511078a
%global llvm_ver 22.1.8
%global llvm_sover %(echo %{llvm_ver} | cut -d. -f1)
%global igc_patch 9

Name:		intel-igc
Version:	2.41.%{igc_patch}
Release:	1
Summary:	Intel Graphics Compiler for OpenCL
Group:		Development/Other
License:	MIT AND Apache-2.0 WITH LLVM-exception
URL:		https://github.com/intel/intel-graphics-compiler
Source0:	%{url}/archive/refs/tags/v%{version}/intel-graphics-compiler-%{version}.tar.gz
Source1:	https://github.com/intel/vc-intrinsics/archive/%{vc_commit}/vc-intrinsics-%{vc_commit}.tar.gz
Source2:	https://github.com/intel/opencl-clang/archive/%{clang_commit}/intel-opencl-clang-%{clang_commit}.tar.gz
Source3:	https://github.com/KhronosGroup/SPIRV-LLVM-Translator/archive/%{translator_commit}/SPIRV-LLVM-Translator-%{translator_commit}.tar.gz
Source4:	https://github.com/KhronosGroup/SPIRV-Headers/archive/%{spirv_headers_commit}/SPIRV-Headers-%{spirv_headers_commit}.tar.gz
Source5:	https://github.com/KhronosGroup/SPIRV-Tools/archive/%{spirv_tools_commit}/SPIRV-Tools-%{spirv_tools_commit}.tar.gz
Source6:	https://github.com/llvm/llvm-project/archive/refs/tags/llvmorg-%{llvm_ver}.tar.gz
Patch0:		0001-Use-Module-print-instead-of-Module-dump.patch

# Intel GPU ISA only. znver1 is OpenMandriva's optimized x86_64.
ExclusiveArch:	x86_64 znver1

BuildRequires:	cmake
BuildRequires:	ninja
BuildRequires:	gcc
BuildRequires:	gcc-c++
BuildRequires:	git-core
BuildRequires:	flex
BuildRequires:	bison
BuildRequires:	python
BuildRequires:	python-mako
BuildRequires:	python-pyyaml
BuildRequires:	chrpath
BuildRequires:	pkgconfig(zlib)
BuildRequires:	pkgconfig(libffi)
BuildRequires:	pkgconfig(libzstd)
BuildRequires:	pkgconfig(libxml-2.0)
BuildRequires:	pkgconfig(libunwind)
BuildRequires:	pkgconfig(SPIRV-Tools)

Requires:	%{name}-libs%{?_isa} = %{EVRD}

Provides:	bundled(intel-vc-intrinsics)
Provides:	bundled(llvm)
Provides:	bundled(opencl-clang)
Provides:	bundled(spirv-llvm-translator)
Provides:	bundled(spirv-headers)
Provides:	bundled(spirv-tools)

%rename intel-graphics-compiler

%description
The Intel Graphics Compiler for OpenCL is an LLVM-based compiler for
OpenCL and Level Zero, targeting Intel graphics hardware.

This build bundles LLVM %{llvm_ver} (statically linked into libigc) because
IGC 2.41 does not support the system LLVM. libopencl-clang.so.%{llvm_sover}
is shipped from intel-igc-libs.

%package	devel
Summary:	Development files for %{name}
Group:		Development/C++
Requires:	%{name}-libs%{?_isa} = %{EVRD}

%description	devel
Headers and link libraries for the Intel Graphics Compiler.

%package	libs
Summary:	Intel Graphics Compiler libraries
Group:		System/Libraries
Requires:	%{name} = %{EVRD}

%description	libs
Runtime libraries for the Intel Graphics Compiler (libigc, libigdfcl,
libiga64 and libopencl-clang).

%prep
tar -xf %{SOURCE1}

%autosetup -n intel-graphics-compiler-%{version} -p1 -S git

mkdir -p %{_builddir}/llvm-project
tar -xf %{SOURCE6} -C %{_builddir}/llvm-project --strip-components=1

rm -rf %{_builddir}/llvm-project/llvm/projects/opencl-clang \
	%{_builddir}/llvm-project/llvm/projects/llvm-spirv
mkdir -p %{_builddir}/llvm-project/llvm/projects/opencl-clang \
	%{_builddir}/llvm-project/llvm/projects/llvm-spirv
tar -xf %{SOURCE2} -C %{_builddir}/llvm-project/llvm/projects/opencl-clang --strip-components=1
tar -xf %{SOURCE3} -C %{_builddir}/llvm-project/llvm/projects/llvm-spirv --strip-components=1

mkdir -p %{_builddir}/SPIRV-Headers %{_builddir}/SPIRV-Tools
tar -xf %{SOURCE4} -C %{_builddir}/SPIRV-Headers --strip-components=1
tar -xf %{SOURCE5} -C %{_builddir}/SPIRV-Tools --strip-components=1

# IGC copies this .git and runs git am for opencl-clang patches.
export GIT_AUTHOR_NAME=build
export GIT_AUTHOR_EMAIL=build@localhost
export GIT_COMMITTER_NAME=build
export GIT_COMMITTER_EMAIL=build@localhost
git -C %{_builddir}/llvm-project init -q
git -C %{_builddir}/llvm-project config user.email "build@localhost"
git -C %{_builddir}/llvm-project config user.name "build"
git -C %{_builddir}/llvm-project config gc.auto 0
git -C %{_builddir}/llvm-project add -f clang/ llvm/docs
git -C %{_builddir}/llvm-project commit -q -m "llvmorg-%{llvm_ver}"

%build
# Source-mode LLVM 22 inside IGC is validated with gcc (the Fedora RHEL build).
export CC=gcc
export CXX=g++
export CMAKE_POLICY_VERSION_MINIMUM=3.5
export CMAKE_GENERATOR=Ninja
export GIT_AUTHOR_NAME=build
export GIT_AUTHOR_EMAIL=build@localhost
export GIT_COMMITTER_NAME=build
export GIT_COMMITTER_EMAIL=build@localhost
# Static LLVM leaves undefined symbols that the OpenCL ICD resolves.
export CFLAGS="%{optflags}"
export CXXFLAGS="%{optflags}"
export LDFLAGS="$(printf '%s' '%{build_ldflags}' | sed -e 's/-Wl,--no-undefined//g')"
%cmake \
	-DCMAKE_BUILD_TYPE=Release \
	-DFETCHCONTENT_FULLY_DISCONNECTED=ON \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
	-DIGC_API_PATCH_VERSION=%{igc_patch} \
	-DIGC_OPTION__ARCHITECTURE_TARGET=Linux64 \
	-DIGC_BUILD__VC_ENABLED=ON \
	-DIGC_OPTION__VC_INTRINSICS_MODE=Source \
	-DVC_INTRINSICS_SRC="%{_builddir}/vc-intrinsics-%{vc_commit}" \
	-DIGC_OPTION__LLVM_PREFERRED_VERSION=%{llvm_ver} \
	-DIGC_OPTION__LLVM_MODE=Source \
	-DIGC_OPTION__SPIRV_TOOLS_MODE=Source \
	-DLLVM_EXTERNAL_SPIRV_HEADERS_SOURCE_DIR="%{_builddir}/SPIRV-Headers"
ninja -v

%install
DESTDIR=%{buildroot} ninja -C build install
for f in %{buildroot}%{_libdir}/libopencl-clang.so.*; do
	chmod 755 "$f"
	chrpath -d "$f" || :
	strip --strip-unneeded "$f"
done
# Static LLVM makes libigdfcl enormous; debuginfo does not need every symbol.
strip --strip-unneeded %{buildroot}%{_libdir}/libigdfcl.so.* || :

%files
%{_bindir}/iga64

%files libs
%license LICENSE.md
%license %{_libdir}/igc2/NOTICES.txt
%dir %{_libdir}/igc2/
%{_libdir}/libiga64.so.2.*
%{_libdir}/libigc.so.2.*
%{_libdir}/libigdfcl.so.2.*
%{_libdir}/libopencl-clang.so.*
%{_includedir}/opencl-c.h
%{_includedir}/opencl-c-base.h

%files devel
%{_libdir}/libiga64.so.2
%{_libdir}/libiga64.so
%{_libdir}/libigc.so.2
%{_libdir}/libigc.so
%{_libdir}/libigdfcl.so.2
%{_libdir}/libigdfcl.so
%{_includedir}/igc
%{_includedir}/iga
%{_includedir}/visa
%{_libdir}/pkgconfig/igc-opencl.pc

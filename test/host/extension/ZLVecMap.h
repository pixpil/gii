#ifndef ZLVECMAP_H
#define ZLVECMAP_H

#include "moai-sim/headers.h"

#include <ciso646>  // detect std::lib
#ifdef _LIBCPP_VERSION
// using libc++
#include <unordered_map>
using namespace std;
#else
// using libstdc++
#include <tr1/unordered_map>
using namespace std;
using namespace std::tr1;
#endif



//----------------------------------------------------------------//
struct hashFunc3D{
    size_t operator()(const ZLVec3D &k) const{
    size_t h1 = hash<float>()(k.mX);
    size_t h2 = hash<float>()(k.mY);
    size_t h3 = hash<float>()(k.mZ);
    return (h1 ^ (h2 << 1)) ^ h3;
    }
};

struct equalsFunc3D{
  bool operator()( const ZLVec3D& lhs, const ZLVec3D& rhs ) const{
    return (lhs.mX == rhs.mX) && (lhs.mY == rhs.mY) && (lhs.mZ == rhs.mZ);
  }
};

// typedef unordered_map<ZLVec3D, int, hashFunc3D, equalsFunc3D> ZLVec3DMap;

//----------------------------------------------------------------//
struct hashFunc2D{
    size_t operator()(const ZLVec2D &k) const{
    size_t h1 = hash<float>()(k.mX);
    size_t h2 = hash<float>()(k.mY);
    return (h1 ^ (h2 << 1));
    }
};

struct equalsFunc2D{
  bool operator()( const ZLVec2D& lhs, const ZLVec2D& rhs ) const{
    return (lhs.mX == rhs.mX) && (lhs.mY == rhs.mY);
  }
};

//----------------------------------------------------------------//
template< typename TYPE >
class ZLVec2DMap :
public unordered_map<ZLVec2D, TYPE, hashFunc2D, equalsFunc2D>
{
public:
  typedef typename unordered_map < ZLVec2D, TYPE, hashFunc2D, equalsFunc2D>::iterator iterator;

  //----------------------------------------------------------------//
  bool contains ( const ZLVec2D& key ) const {
    return ( this->find ( key ) != this->end ());
  }
};

template< typename TYPE >
class ZLVec3DMap :
public unordered_map<ZLVec3D, TYPE, hashFunc3D, equalsFunc3D>
{
public:
  typedef typename unordered_map < ZLVec3D, TYPE, hashFunc3D, equalsFunc3D>::iterator iterator;

  //----------------------------------------------------------------//
  bool contains ( const ZLVec3D& key ) const {
    return ( this->find ( key ) != this->end ());
  } 
};


#endif
